import type { AskResponse, Draft, Severity, Source, TraceEvent, ValidationReport, Verdict } from "@/lib/api";
import { Markdown } from "./Markdown";

type Cite = (n: number) => void;

const VERDICT: Record<Verdict, { label: string; className: string }> = {
  approved: { label: "Approved", className: "bg-emerald-100 text-emerald-900 ring-emerald-300" },
  approved_with_warnings: {
    label: "Approved with warnings",
    className: "bg-amber-100 text-amber-900 ring-amber-300",
  },
  needs_more_info: { label: "Needs more information", className: "bg-sky-100 text-sky-900 ring-sky-300" },
  rejected: { label: "Rejected", className: "bg-red-100 text-red-900 ring-red-300" },
};

const SEVERITY: Record<Severity, string> = {
  critical: "bg-red-600 text-white",
  major: "bg-amber-500 text-amber-950",
  minor: "bg-slate-200 text-slate-800",
};

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const v = VERDICT[verdict];
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-sm font-semibold ring-1 ${v.className}`}>
      {v.label}
    </span>
  );
}

function describeCall(name: string, args: Record<string, unknown>): string {
  if (name === "build_context") {
    const filters = [args.drugs, args.sections]
      .filter((f): f is string[] => Array.isArray(f) && f.length > 0)
      .map((f) => f.join(", "));
    return `Search labels: “${String(args.query ?? "")}”${filters.length ? ` (${filters.join(" · ")})` : ""}`;
  }
  if (name === "validate_prescription") {
    const items = Array.isArray(args.prescription) ? (args.prescription as { drug?: string; dose?: string }[]) : [];
    return `Validate prescription: ${items.map((i) => `${i.drug ?? "?"} ${i.dose ?? ""}`.trim()).join(", ")}`;
  }
  if (name === "write_prescription") return `Draft prescription: “${String(args.description ?? "")}”`;
  return name;
}

function traceLine(e: TraceEvent, i: number) {
  switch (e.event) {
    case "plan":
      return (
        <li key={i}>
          <span className="font-medium">Plan</span>
          <ol className="mt-1 list-decimal pl-5 text-slate-600">
            {e.data.steps.map((s, j) => (
              <li key={j}>{s}</li>
            ))}
          </ol>
        </li>
      );
    case "tool_call":
      return e.data.calls.map((c, j) => (
        <li key={`${i}-${j}`}>
          <span className="font-mono text-xs text-teal-800">{c.name}</span> {describeCall(c.name, c.args)}
        </li>
      ));
    case "tool_result":
      return (
        <li key={i} className="text-slate-600">
          ↳ {e.data.name}:{" "}
          {e.data.status === "error" ? (
            <span className="text-red-700">failed (the agent will adapt)</span>
          ) : (
            `${e.data.source_ids.length} passage${e.data.source_ids.length === 1 ? "" : "s"}`
          )}
          {e.data.verdict && (
            <>
              {" "}
              · <VerdictBadge verdict={e.data.verdict} />
            </>
          )}
        </li>
      );
    case "review":
      return (
        <li key={i}>
          <span className="font-medium">Critic:</span>{" "}
          {e.data.verdict === "approve"
            ? "grounding check passed"
            : `${e.data.unsupported_claims.length} unsupported claim(s) — ${e.data.revising ? "revising" : "flagged in the answer"}`}
        </li>
      );
    case "final":
      return (
        <li key={i} className="font-medium text-emerald-800">
          Answer ready
        </li>
      );
    case "error":
      return null; // shown as the error banner
  }
}

export function Trace({ events, running }: { events: TraceEvent[]; running: boolean }) {
  return (
    <section aria-labelledby="trace-title" className="rounded-lg border border-slate-200 bg-white p-4">
      <h2 id="trace-title" className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
        Agent trace
      </h2>
      <ol className="space-y-1.5 text-sm" aria-live="polite">
        {events.map(traceLine)}
        {running && (
          <li className="flex items-center gap-2 text-slate-500">
            <span className="h-2 w-2 animate-pulse rounded-full bg-teal-600" aria-hidden />
            Working… (complex questions can take a minute)
          </li>
        )}
      </ol>
    </section>
  );
}

function CiteIds({ ids, citations, onCite }: { ids: string[]; citations: Source[]; onCite: Cite }) {
  return ids.map((id) => {
    const n = citations.findIndex((c) => c.id === id) + 1;
    return n ? (
      <button
        key={id}
        type="button"
        onClick={() => onCite(n)}
        className="ml-1 rounded bg-teal-100 px-1 text-xs font-semibold text-teal-900 hover:bg-teal-200"
        aria-label={`Show source ${n}`}
      >
        {n}
      </button>
    ) : (
      <span key={id} className="ml-1 font-mono text-xs text-slate-500">
        {id}
      </span>
    );
  });
}

function ValidationCard({ report, citations, onCite }: { report: ValidationReport; citations: Source[]; onCite: Cite }) {
  return (
    <section aria-labelledby="validation-title" className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <h2 id="validation-title" className="font-semibold">
          Prescription check
        </h2>
        <VerdictBadge verdict={report.verdict} />
      </div>
      <p className="mb-3 text-sm text-slate-700">{report.summary}</p>
      {report.issues.length > 0 && (
        <ul className="space-y-2 text-sm">
          {report.issues.map((issue, i) => (
            <li key={i} className="flex gap-2">
              <span className={`h-fit shrink-0 rounded px-1.5 text-xs font-semibold uppercase ${SEVERITY[issue.severity]}`}>
                {issue.severity}
              </span>
              <span>
                <span className="font-medium">
                  {issue.category.replace(/_/g, " ")}
                  {issue.drug ? ` · ${issue.drug}` : ""}:
                </span>{" "}
                {issue.message}
                <CiteIds ids={issue.source_ids} citations={citations} onCite={onCite} />
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function DraftCard({ draft }: { draft: Draft }) {
  return (
    <section aria-labelledby="draft-title" className="rounded-lg border border-slate-200 bg-white p-4">
      <h2 id="draft-title" className="mb-2 font-semibold">
        Draft prescription
      </h2>
      {draft.items.length ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-slate-500">
              <tr>
                <th className="py-1 pr-3 font-medium">Drug</th>
                <th className="py-1 pr-3 font-medium">Dose</th>
                <th className="py-1 pr-3 font-medium">Route</th>
                <th className="py-1 pr-3 font-medium">Frequency</th>
                <th className="py-1 font-medium">Duration</th>
              </tr>
            </thead>
            <tbody>
              {draft.items.map((it, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="py-1 pr-3 font-medium">{it.drug}</td>
                  <td className="py-1 pr-3">{it.dose}</td>
                  <td className="py-1 pr-3">{it.route}</td>
                  <td className="py-1 pr-3">{it.frequency}</td>
                  <td className="py-1">{it.duration ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-sm text-slate-600">No corpus drug fits this request.</p>
      )}
    </section>
  );
}

function Passages({ citations }: { citations: Source[] }) {
  if (!citations.length) return null;
  return (
    <section aria-labelledby="passages-title" className="rounded-lg border border-slate-200 bg-white p-4">
      <h2 id="passages-title" className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
        Cited passages
      </h2>
      <div className="space-y-2">
        {citations.map((s, i) => (
          <details key={s.id} id={`src-${i + 1}`} className="group rounded border border-slate-200 open:bg-slate-50">
            <summary className="cursor-pointer px-3 py-2 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-600">
              <span className="font-semibold">[{i + 1}]</span> {s.file} — <span className="text-slate-600">{s.heading}</span>
            </summary>
            <div className="border-t border-slate-200 px-3 py-2 text-sm">
              <p className="whitespace-pre-line text-slate-700">{s.text}</p>
              {s.url && (
                <a href={s.url} target="_blank" rel="noreferrer" className="mt-2 inline-block text-teal-800 underline">
                  Open original label
                </a>
              )}
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}

export function Result({ result, onCite }: { result: AskResponse; onCite: Cite }) {
  return (
    <>
      {result.validation && (
        <ValidationCard report={result.validation} citations={result.citations} onCite={onCite} />
      )}
      {result.draft && <DraftCard draft={result.draft} />}
      <section aria-labelledby="answer-title" className="rounded-lg border border-slate-200 bg-white p-4">
        <h2 id="answer-title" className="mb-2 font-semibold">
          Answer
        </h2>
        <Markdown text={result.answer} onCite={onCite} />
      </section>
      <Passages citations={result.citations} />
    </>
  );
}
