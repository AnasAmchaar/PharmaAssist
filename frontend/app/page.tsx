"use client";

import { useEffect, useRef, useState, type ClipboardEvent, type DragEvent, type FormEvent } from "react";
import { Icon, Logo, type ICONS } from "@/components/Icons";
import { EMPTY_PATIENT, PatientForm, summarizePatient, toPatient, type PatientFields } from "@/components/PatientForm";
import { Result, Trace } from "@/components/Results";
import { streamAsk, type AskResponse, type TraceEvent } from "@/lib/api";
import { MAX_IMAGES, toAttachment, type Attachment } from "@/lib/images";

// One request box: the agent decides from the wording (and any attached image) whether to search the
// labels, check a prescription or draft one. Examples are plain language, with no hint about the tool.
type Example = { label: string; question: string; patient?: Partial<PatientFields>; image?: string };
const EXAMPLES: { group: string; icon: keyof typeof ICONS; items: Example[] }[] = [
  {
    group: "Ask about a drug",
    icon: "search",
    items: [
      { label: "Main contraindications of warfarin", question: "What are the main contraindications for warfarin?" },
      {
        label: "Warfarin vs apixaban contraindications",
        question:
          "Compare the contraindications of warfarin and apixaban. What conditions are shared and which are unique to each drug?",
      },
      {
        label: "Bleeding risk: warfarin + sertraline",
        question:
          "A patient currently on warfarin is prescribed sertraline. What is the risk of bleeding and what monitoring is recommended?",
      },
      {
        label: "Metformin at an eGFR of 25",
        question:
          "A patient with an eGFR of 25 mL/min is being considered for metformin. Is metformin contraindicated at this level of renal function, and what is the threshold?",
      },
    ],
  },
  {
    group: "Check a prescription",
    icon: "shield",
    items: [
      {
        label: "Prescription photo, kidney disease",
        question: "Is this prescription safe for my patient?",
        patient: { age: "67", sex: "male", egfr: "25", hepatic_impairment: "none" },
        image: "/examples/rx-metformin.png",
      },
      {
        label: "Sertraline for a patient on warfarin",
        question: "I'd like to prescribe sertraline 50 mg once daily for this patient. Any problems?",
        patient: { age: "58", sex: "male", egfr: "80", hepatic_impairment: "none", current_medications: "warfarin" },
      },
    ],
  },
  {
    group: "Suggest a prescription",
    icon: "pencil",
    items: [
      {
        label: "Newly diagnosed type 2 diabetes",
        question: "What should I prescribe this patient for newly diagnosed type 2 diabetes?",
        patient: { age: "60", sex: "female", egfr: "75", hepatic_impairment: "none", pregnant: "no", breastfeeding: "no" },
      },
    ],
  },
];

const IMAGE_ONLY_QUESTION = "Please review the attached image.";

type Submitted = { question: string; images: Attachment[]; patient: string[] };
type Run = {
  events: TraceEvent[];
  result: AskResponse | null;
  error: string | null;
  running: boolean;
  startedAt: number;
  endedAt: number;
};
const IDLE: Run = { events: [], result: null, error: null, running: false, startedAt: 0, endedAt: 0 };

export default function Home() {
  const [question, setQuestion] = useState("");
  const [images, setImages] = useState<Attachment[]>([]);
  const [patient, setPatient] = useState<PatientFields>(EMPTY_PATIENT);
  const [patientOpen, setPatientOpen] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState<Submitted | null>(null);
  const [run, setRun] = useState<Run>(IDLE);
  const [now, setNow] = useState(0);
  const abort = useRef<AbortController | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const form = useRef<HTMLFormElement>(null);
  const results = useRef<HTMLDivElement>(null);
  const chips = summarizePatient(patient);

  useEffect(() => {
    if (!run.running) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [run.running]);
  const seconds = run.startedAt ? Math.max(0, Math.round(((run.running ? now : run.endedAt) - run.startedAt) / 1000)) : 0;

  async function addFiles(files: FileList | File[]) {
    const picked = Array.from(files).filter((f) => f.type.startsWith("image/"));
    if (!picked.length) return;
    const room = MAX_IMAGES - images.length;
    if (room <= 0) return setNotice(`At most ${MAX_IMAGES} images per request.`);
    setNotice(picked.length > room ? `Only the first ${room} image(s) were added (max ${MAX_IMAGES}).` : null);
    try {
      const added = await Promise.all(picked.slice(0, room).map(toAttachment));
      setImages((prev) => [...prev, ...added].slice(0, MAX_IMAGES));
    } catch (err) {
      setNotice(err instanceof Error ? err.message : String(err));
    }
  }

  async function loadExample(ex: Example) {
    setQuestion(ex.question);
    // Each example brings its own patient and image (or none), so nothing leaks in from an earlier one.
    setPatient({ ...EMPTY_PATIENT, ...ex.patient });
    setPatientOpen(false);
    setNotice(null);
    setImages([]);
    if (ex.image) {
      try {
        const res = await fetch(ex.image);
        if (!res.ok) throw new Error(`Could not load the example image (HTTP ${res.status}).`);
        const blob = await res.blob();
        setImages([await toAttachment(new File([blob], ex.image.split("/").pop() ?? "example.png", { type: blob.type }))]);
      } catch (err) {
        setNotice(err instanceof Error ? err.message : String(err));
      }
    }
  }

  async function submit(e?: FormEvent) {
    e?.preventDefault();
    const text = question.trim() || (images.length ? IMAGE_ONLY_QUESTION : "");
    if (!text) return setNotice("Type a request or attach an image.");
    setNotice(null);
    abort.current?.abort();
    const ctrl = new AbortController();
    abort.current = ctrl;
    const start = Date.now();
    setNow(start);
    setSubmitted({ question: text, images, patient: chips });
    setRun({ ...IDLE, running: true, startedAt: start });
    if (window.innerWidth < 1024) results.current?.scrollIntoView({ behavior: "smooth" });
    const update = (fn: (r: Run) => Run) => {
      if (abort.current === ctrl) setRun(fn); // ignore events from a superseded run
    };
    try {
      await streamAsk(
        { question: text, patient: toPatient(patient), images: images.map((i) => i.url) },
        (ev) =>
          update((r) => ({
            ...r,
            events: [...r.events, ev],
            result: ev.event === "final" ? ev.data : r.result,
            error: ev.event === "error" ? ev.data.message : r.error,
          })),
        ctrl.signal,
      );
    } catch (err) {
      if (!ctrl.signal.aborted) update((r) => ({ ...r, error: err instanceof Error ? err.message : String(err) }));
    } finally {
      update((r) => ({ ...r, running: false, endedAt: Date.now() }));
    }
  }

  function cancel() {
    abort.current?.abort();
    abort.current = null;
    setRun((r) => ({ ...r, running: false, endedAt: Date.now(), error: "Cancelled." }));
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    addFiles(e.dataTransfer.files);
  }

  function onPaste(e: ClipboardEvent) {
    if (e.clipboardData.files.length) {
      e.preventDefault();
      addFiles(e.clipboardData.files);
    }
  }

  function cite(n: number) {
    const el = document.getElementById(`src-${n}`) as HTMLDetailsElement | null;
    if (!el) return;
    el.open = true;
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.querySelector("summary")?.focus();
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/85 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-3">
            <Logo />
            <div>
              <h1 className="text-lg font-semibold leading-tight tracking-tight">
                Pharma<span className="text-teal-700">Assist</span>
              </h1>
              <p className="hidden text-xs text-slate-500 sm:block">
                Grounded in FDA DailyMed labels &amp; MedlinePlus monographs · 10 drugs · every claim cited
              </p>
            </div>
          </div>
          <p role="note" className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-900 ring-1 ring-amber-200">
            Not medical advice
          </p>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[minmax(0,26rem)_minmax(0,1fr)] lg:gap-8 lg:py-8">
        {/* Sticky on wide screens; scrolls on its own when taller than the window (patient panel open). */}
        <aside className="space-y-5 lg:sticky lg:top-24 lg:max-h-[calc(100vh-7rem)] lg:self-start lg:overflow-y-auto lg:p-1 lg:-m-1">
          <form
            ref={form}
            onSubmit={submit}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            className={`relative rounded-2xl border bg-white shadow-sm transition ${
              dragging ? "border-teal-500 ring-4 ring-teal-500/15" : "border-slate-200"
            }`}
          >
            {dragging && (
              <div className="pointer-events-none absolute inset-0 z-10 grid place-items-center rounded-2xl bg-teal-50/90 text-sm font-medium text-teal-800">
                Drop images to attach
              </div>
            )}
            <label htmlFor="question" className="sr-only">
              Your request
            </label>
            <textarea
              id="question"
              maxLength={4000}
              rows={5}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onPaste={onPaste}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  form.current?.requestSubmit();
                }
              }}
              className="block w-full resize-none rounded-t-2xl border-0 bg-transparent px-4 pt-4 text-[0.95rem] leading-relaxed placeholder:text-slate-400 focus:outline-none focus:ring-0"
              placeholder="Ask about a drug, check whether a prescription is safe for your patient, or ask what to prescribe. You can attach a photo of a prescription or label."
              aria-describedby="composer-hint"
            />

            {images.length > 0 && (
              <ul className="flex flex-wrap gap-2 px-4 pb-2" aria-label="Attached images">
                {images.map((img, i) => (
                  <li key={img.id} className="group relative">
                    {/* eslint-disable-next-line @next/next/no-img-element -- local data URL preview */}
                    <img src={img.url} alt={`Attached image ${i + 1}: ${img.name}`} className="h-16 w-16 rounded-lg object-cover ring-1 ring-slate-200" />
                    <button
                      type="button"
                      onClick={() => setImages(images.filter((x) => x.id !== img.id))}
                      aria-label={`Remove image ${i + 1}`}
                      className="absolute -right-1.5 -top-1.5 grid h-5 w-5 place-items-center rounded-full bg-slate-800 text-white shadow hover:bg-slate-900"
                    >
                      <Icon name="x" className="h-3 w-3" />
                    </button>
                  </li>
                ))}
              </ul>
            )}

            {chips.length > 0 && !patientOpen && (
              <div className="flex flex-wrap items-center gap-1.5 px-4 pb-3">
                <span className="text-xs font-medium text-slate-500">Patient:</span>
                {chips.map((c) => (
                  <span key={c} className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
                    {c}
                  </span>
                ))}
              </div>
            )}

            <div className="flex items-center gap-1 border-t border-slate-100 px-2 py-2">
              <input
                ref={fileInput}
                type="file"
                accept="image/png,image/jpeg,image/webp,image/gif"
                multiple
                className="hidden"
                onChange={(e) => {
                  if (e.target.files) addFiles(e.target.files);
                  e.target.value = "";
                }}
              />
              <button
                type="button"
                onClick={() => fileInput.current?.click()}
                disabled={images.length >= MAX_IMAGES}
                className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-slate-600 hover:bg-slate-100 hover:text-slate-900 disabled:opacity-40"
              >
                <Icon name="photo" className="h-4 w-4" />
                Image
              </button>
              <button
                type="button"
                onClick={() => setPatientOpen(!patientOpen)}
                aria-expanded={patientOpen}
                aria-controls="patient-panel"
                className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm hover:bg-slate-100 hover:text-slate-900 ${
                  chips.length ? "text-teal-700" : "text-slate-600"
                }`}
              >
                <Icon name="user" className="h-4 w-4" />
                Patient{chips.length ? ` (${chips.length})` : ""}
              </button>
              <span id="composer-hint" className="ml-auto hidden pr-2 text-xs text-slate-400 sm:inline">
                Ctrl + Enter
              </span>
              {run.running ? (
                <button
                  type="button"
                  onClick={cancel}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-slate-800 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-900"
                >
                  <Icon name="stop" className="h-4 w-4" /> Stop
                </button>
              ) : (
                <button
                  type="submit"
                  className="ml-auto inline-flex items-center gap-1.5 rounded-xl bg-teal-700 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-teal-800 focus:outline-none focus-visible:ring-4 focus-visible:ring-teal-600/30 sm:ml-0"
                >
                  Ask <Icon name="send" className="h-4 w-4" />
                </button>
              )}
            </div>

            {patientOpen && (
              <div id="patient-panel" className="border-t border-slate-100 px-4 py-4">
                <PatientForm value={patient} onChange={setPatient} />
                {chips.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setPatient(EMPTY_PATIENT)}
                    className="mt-3 text-xs font-medium text-slate-500 underline-offset-2 hover:text-slate-800 hover:underline"
                  >
                    Clear patient details
                  </button>
                )}
              </div>
            )}
          </form>

          {notice && (
            <p role="status" className="rounded-xl bg-amber-50 px-3 py-2 text-sm text-amber-900 ring-1 ring-amber-200">
              {notice}
            </p>
          )}

          <section aria-labelledby="examples-title" className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <h2 id="examples-title" className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Try an example
            </h2>
            <div className="space-y-4">
              {EXAMPLES.map((g) => (
                <div key={g.group}>
                  <p className="mb-1 flex items-center gap-1.5 text-xs font-medium text-slate-600">
                    <Icon name={g.icon} className="h-3.5 w-3.5 text-teal-700" /> {g.group}
                  </p>
                  <ul>
                    {g.items.map((ex) => (
                      <li key={ex.label}>
                        <button
                          type="button"
                          title={ex.question}
                          onClick={() => loadExample(ex)}
                          className="group flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm text-slate-700 hover:bg-teal-50 hover:text-teal-900"
                        >
                          <span className="flex-1">{ex.label}</span>
                          {ex.image && <Icon name="photo" className="h-4 w-4 text-slate-400" />}
                          {ex.patient && <Icon name="user" className="h-4 w-4 text-slate-400" />}
                          <Icon name="chevron" className="h-3.5 w-3.5 text-slate-300 group-hover:text-teal-700" />
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>
        </aside>

        <div ref={results} className="min-w-0 scroll-mt-24 space-y-5">
          {submitted ? (
            <>
              <section aria-label="Your request" className="rounded-2xl bg-slate-800 p-5 text-slate-100 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">You asked</p>
                <p className="mt-1 whitespace-pre-line text-[0.95rem]">{submitted.question}</p>
                {(submitted.images.length > 0 || submitted.patient.length > 0) && (
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    {submitted.images.map((img, i) => (
                      // eslint-disable-next-line @next/next/no-img-element -- local data URL preview
                      <img key={img.id} src={img.url} alt={`Attached image ${i + 1}`} className="h-12 w-12 rounded-md object-cover ring-1 ring-white/20" />
                    ))}
                    {submitted.patient.map((c) => (
                      <span key={c} className="rounded-full bg-white/10 px-2 py-0.5 text-xs text-slate-200">
                        {c}
                      </span>
                    ))}
                  </div>
                )}
              </section>
              {run.error && (
                <p role="alert" className="flex items-start gap-2 rounded-2xl bg-red-50 p-4 text-sm text-red-800 ring-1 ring-red-200">
                  <Icon name="xCircle" className="h-5 w-5 shrink-0" />
                  {run.error}
                </p>
              )}
              {(run.running || run.events.length > 0) && <Trace events={run.events} running={run.running} seconds={seconds} />}
              {run.result && <Result result={run.result} onCite={cite} />}
            </>
          ) : (
            <EmptyState />
          )}
        </div>
      </main>
    </div>
  );
}

const HOW: { icon: keyof typeof ICONS; title: string; text: string }[] = [
  { icon: "list", title: "Plan", text: "Breaks your request into steps." },
  { icon: "search", title: "Retrieve & use tools", text: "Searches the labels, checks or drafts prescriptions; it picks the tools itself." },
  { icon: "shield", title: "Review", text: "A critic checks every claim against the retrieved passages." },
  { icon: "document", title: "Answer", text: "Cited to the source files, with reviewer notes and a disclaimer." },
];

const DRUGS = ["acetaminophen", "albuterol", "amoxicillin", "apixaban", "aspirin", "atorvastatin", "ibuprofen", "metformin", "sertraline", "warfarin"];

function EmptyState() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
      <div className="flex items-center gap-2 text-teal-700">
        <Icon name="sparkles" className="h-5 w-5" />
        <p className="text-xs font-semibold uppercase tracking-wider">Agentic pharmacology research</p>
      </div>
      <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">Ask, check or draft — the agent does the rest.</h2>
      <p className="mt-2 max-w-2xl text-sm text-slate-600">
        Type a question, describe a prescription, or attach a photo of one. Add patient details for safety checks. You
        will see each step as the agent works.
      </p>
      <ol className="mt-6 grid gap-3 sm:grid-cols-2">
        {HOW.map((h, i) => (
          <li key={h.title} className="flex gap-3 rounded-xl bg-slate-50 p-4 ring-1 ring-slate-100">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-white text-teal-700 shadow-sm ring-1 ring-slate-200">
              <Icon name={h.icon} className="h-5 w-5" />
            </span>
            <span>
              <span className="block text-sm font-semibold text-slate-900">
                {i + 1}. {h.title}
              </span>
              <span className="block text-sm text-slate-600">{h.text}</span>
            </span>
          </li>
        ))}
      </ol>
      <div className="mt-6">
        <p className="mb-2 text-xs font-medium text-slate-500">Drugs in the corpus</p>
        <div className="flex flex-wrap gap-1.5">
          {DRUGS.map((d) => (
            <span key={d} className="rounded-full bg-teal-50 px-2.5 py-1 text-xs font-medium text-teal-800 ring-1 ring-teal-100">
              {d}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
