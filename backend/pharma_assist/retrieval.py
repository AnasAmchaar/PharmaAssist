"""Heading-aware markdown chunking + in-memory hybrid retrieval (cosine + BM25, fused with RRF)."""

import hashlib
import re
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from langchain_core.embeddings import Embeddings
from rank_bm25 import BM25Okapi

from pharma_assist.config import get_settings
from pharma_assist.llm import get_embeddings

MAX_WORDS = 300  # long label sections (up to ~2.5k words) are split on line/sentence boundaries
RRF_K = 60  # standard Reciprocal Rank Fusion constant

# Canonical section tag from the top-level (`##`) heading. First match wins, so order matters
# ("10 OVERDOSAGE" must hit overdose before dosage). Covers DailyMed Rx (numbered), DailyMed OTC
# ("Uses", "Directions", "Warnings") and MedlinePlus Q&A headings.
_SECTION_RULES: list[tuple[str, re.Pattern[str]]] = [
    (tag, re.compile(pattern, re.IGNORECASE))
    for tag, pattern in [
        ("contraindications", r"contraindicat"),
        ("interactions", r"interaction"),
        ("overdose", r"overdos|emergency"),
        ("adverse_reactions", r"adverse reaction|side effect"),
        (
            "specific_populations",
            r"specific population|pregnan|nursing|lactation|labor and delivery|pediatric|geriatric",
        ),
        ("indications", r"indication|\buses\b|why is this medication prescribed"),
        ("dosage", r"dosage|directions|how should this medicine be used|forget a dose"),
        ("warnings", r"warning|precaution"),
        ("pharmacology", r"pharmacolog|pharmacokinetic|pharmacodynamic|mechanism"),
    ]
]
SECTIONS = (*(tag for tag, _ in _SECTION_RULES), "other")

_HEADING = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_SOURCE_URL = re.compile(r"^Source:\s*(\S+)", re.MULTILINE)
_TOKEN = re.compile(r"[a-z0-9]+")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")


@dataclass(frozen=True)
class Chunk:
    id: str  # "dailymed-warfarin.md#7"
    file: str  # "dailymed-warfarin.md"
    drug: str | None  # "warfarin"; None for GLOSSARY.md
    url: str | None  # upstream DailyMed / MedlinePlus page
    heading: str  # "Warfarin (DailyMed label) › 4 CONTRAINDICATIONS"
    section: str  # one of SECTIONS
    text: str

    @property
    def content(self) -> str:
        """What gets embedded and BM25-indexed: the heading path gives each chunk its drug/section context."""
        return f"{self.heading}\n{self.text}"


def canonical_section(heading: str) -> str:
    return next((tag for tag, rx in _SECTION_RULES if rx.search(heading)), "other")


def _split(text: str, max_words: int = MAX_WORDS) -> list[str]:
    """Pack lines into ~max_words parts; lines that are too long (many labels are one line per
    section) are broken into sentences first. A single over-long sentence stays whole."""
    units: list[str] = []
    for line in text.splitlines():
        if line.strip():
            units.extend(_SENTENCE_END.split(line) if len(line.split()) > max_words else [line])
    parts: list[str] = []
    current: list[str] = []
    words = 0
    for unit in units:
        n = len(unit.split())
        if current and words + n > max_words:
            parts.append("\n".join(current))
            current, words = [], 0
        current.append(unit)
        words += n
    if current:
        parts.append("\n".join(current))
    return parts


def chunk_markdown(file: str, text: str) -> list[Chunk]:
    """One chunk per heading block (split further if long), carrying the full heading path."""
    stem_parts = Path(file).stem.split("-", 1)
    drug = stem_parts[1].lower() if len(stem_parts) == 2 else None
    url = m.group(1) if (m := _SOURCE_URL.search(text)) else None

    blocks: list[tuple[list[str], str]] = []
    path: list[str] = []
    body: list[str] = []

    def flush() -> None:
        content = "\n".join(body).strip()
        if content:
            blocks.append((list(path), content))
        body.clear()

    for line in text.splitlines():
        if m := _HEADING.match(line):
            flush()
            del path[len(m.group(1)) - 1 :]
            path.append(m.group(2))
        elif not line.startswith("Source:"):
            body.append(line)
    flush()

    chunks: list[Chunk] = []
    for heading_path, content in blocks:
        section = canonical_section(heading_path[1]) if len(heading_path) > 1 else "other"
        for part in _split(content):
            chunks.append(
                Chunk(
                    id=f"{file}#{len(chunks)}",
                    file=file,
                    drug=drug,
                    url=url,
                    heading=" › ".join(heading_path),
                    section=section,
                    text=part,
                )
            )
    return chunks


def load_corpus(corpus_dir: Path) -> list[Chunk]:
    files = sorted(corpus_dir.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"No .md files found in corpus dir {corpus_dir}")
    return [c for f in files for c in chunk_markdown(f.name, f.read_text(encoding="utf-8"))]


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def _rrf(scores: np.ndarray, positive_only: bool = False) -> np.ndarray:
    ranks = np.empty(len(scores))
    ranks[np.argsort(-scores, kind="stable")] = np.arange(1, len(scores) + 1)
    fused = 1.0 / (RRF_K + ranks)
    # BM25 gives 0 to chunks sharing no query term; don't let corpus order rank them.
    return np.where(scores > 0, fused, 0.0) if positive_only else fused


class HybridIndex:
    """In-memory index: dense cosine (normalized numpy matrix) + BM25, fused with RRF."""

    def __init__(self, chunks: list[Chunk], embeddings: Embeddings, cache_dir: Path) -> None:
        self.chunks = chunks
        self.drugs = sorted({c.drug for c in chunks if c.drug})
        self._embeddings = embeddings
        self._bm25 = BM25Okapi([_tokens(c.content) for c in chunks])
        vectors = self._load_or_embed(cache_dir)
        self._vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

    def _load_or_embed(self, cache_dir: Path) -> np.ndarray:
        # Key on the chunk texts (not raw files) so chunker changes also invalidate the cache.
        h = hashlib.sha256(getattr(self._embeddings, "model", "").encode())
        for c in self.chunks:
            h.update(b"\0" + c.content.encode())
        path = cache_dir / f"emb-{h.hexdigest()[:16]}.npy"
        if path.exists():
            vectors = np.load(path)
            if vectors.shape[0] == len(self.chunks):
                return vectors
        vectors = np.asarray(self._embeddings.embed_documents([c.content for c in self.chunks]), np.float32)
        cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with tmp.open("wb") as f:  # write-then-rename so a crash never leaves a truncated cache
            np.save(f, vectors)
        tmp.replace(path)
        return vectors

    def search(
        self,
        query: str,
        k: int = 6,
        drugs: list[str] | None = None,
        sections: list[str] | None = None,
    ) -> list[tuple[Chunk, float]]:
        """Top-k chunks by RRF of cosine and BM25 ranks, after optional drug/section filters."""
        mask = np.ones(len(self.chunks), dtype=bool)
        if drugs:
            wanted = {d.strip().lower() for d in drugs}
            mask &= np.array([c.drug in wanted for c in self.chunks])
        if sections:
            mask &= np.array([c.section in sections for c in self.chunks])
        candidates = np.flatnonzero(mask)
        if not candidates.size or k <= 0 or not query.strip():
            return []

        q = np.asarray(self._embeddings.embed_query(query), np.float32)
        dense = self._vectors[candidates] @ (q / np.linalg.norm(q))
        sparse = self._bm25.get_scores(_tokens(query))[candidates]
        fused = _rrf(dense) + _rrf(sparse, positive_only=True)
        top = np.argsort(-fused, kind="stable")[:k]
        return [(self.chunks[candidates[i]], float(fused[i])) for i in top]


_index: HybridIndex | None = None
_index_lock = threading.Lock()


def get_index() -> HybridIndex:
    """Process-wide index, built once. The lock makes concurrent first callers wait for one build."""
    global _index
    with _index_lock:
        if _index is None:
            s = get_settings()
            _index = HybridIndex(load_corpus(s.corpus_dir), get_embeddings(), s.cache_dir)
    return _index


def index_ready() -> bool:
    return _index is not None
