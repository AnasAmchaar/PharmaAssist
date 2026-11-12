"use client";

import { useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { EMPTY_PATIENT, PatientForm, toPatient, type PatientFields } from "@/components/PatientForm";
import { Result, Trace } from "@/components/Results";
import { CORPUS_DRUGS, streamAsk, type AskResponse, type TraceEvent } from "@/lib/api";

type Tab = "ask" | "validate" | "write";
const TABS: { id: Tab; label: string }[] = [
  { id: "ask", label: "Ask" },
  { id: "validate", label: "Validate" },
  { id: "write", label: "Write" },
];

// The four public evaluation questions from the assignment.
const EXAMPLES = [
  "What are the main contraindications for warfarin?",
  "Compare the contraindications of warfarin and apixaban. What conditions are shared and which are unique to each drug?",
  "A patient currently on warfarin is prescribed sertraline. What is the risk of bleeding and what monitoring is recommended?",
  "A patient with an eGFR of 25 mL/min is being considered for metformin. Is metformin contraindicated at this level of renal function, and what is the threshold?",
];

type Rx = { drug: string; dose: string; frequency: string };
const EMPTY_RX: Rx = { drug: "", dose: "", frequency: "" };
const MAX_RX = 10;

type Run = { events: TraceEvent[]; result: AskResponse | null; error: string | null; running: boolean };
const IDLE: Run = { events: [], result: null, error: null, running: false };

const input =
  "w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600";
const chip =
  "rounded-full border border-slate-300 bg-white px-3 py-1 text-left text-xs text-slate-700 hover:border-teal-600 hover:text-teal-800";

export default function Home() {
  const [tab, setTab] = useState<Tab>("ask");
  const [question, setQuestion] = useState("");
  const [rx, setRx] = useState<Rx[]>([EMPTY_RX]);
  const [description, setDescription] = useState("");
  const [patient, setPatient] = useState<PatientFields>(EMPTY_PATIENT);
  const [run, setRun] = useState<Run>(IDLE);
  const abort = useRef<AbortController | null>(null);

  async function start(q: string) {
    abort.current?.abort();
    const ctrl = new AbortController();
    abort.current = ctrl;
    setRun({ ...IDLE, running: true });
    const update = (fn: (r: Run) => Run) => {
      if (abort.current === ctrl) setRun(fn); // ignore events from a superseded run
    };
    try {
      await streamAsk(
        { question: q, patient: toPatient(patient) },
        (e) =>
          update((r) => ({
            ...r,
            events: [...r.events, e],
            result: e.event === "final" ? e.data : r.result,
            error: e.event === "error" ? e.data.message : r.error,
          })),
        ctrl.signal,
      );
    } catch (err) {
      if (!ctrl.signal.aborted) update((r) => ({ ...r, error: err instanceof Error ? err.message : String(err) }));
    } finally {
      update((r) => ({ ...r, running: false }));
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    if (tab === "ask") start(question.trim());
    else if (tab === "validate") {
      const items = rx.map((r) => `${r.drug.trim()} ${r.dose.trim()} ${r.frequency.trim()}`).join("; ");
      start(`Validate this prescription for the patient: ${items}.`);
    } else start(`Write a prescription for this request and validate it for the patient: ${description.trim()}`);
  }

  function cancel() {
    abort.current?.abort();
    abort.current = null;
    setRun((r) => ({ ...r, running: false, error: "Cancelled." }));
  }

  function onTabKey(e: KeyboardEvent, i: number) {
    const next = e.key === "ArrowRight" ? i + 1 : e.key === "ArrowLeft" ? i - 1 : null;
    if (next === null) return;
    const t = TABS[(next + TABS.length) % TABS.length];
    setTab(t.id);
    document.getElementById(`tab-${t.id}`)?.focus();
  }

  const setRow = (i: number, key: keyof Rx, v: string) => setRx(rx.map((r, j) => (j === i ? { ...r, [key]: v } : r)));
  const showPatient = tab !== "ask";
  // The patient form is shared by all tabs, so say when it will be sent with a plain question.
  const hasPatient = toPatient(patient) !== null;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-4">
          <h1 className="text-xl font-semibold">
            Pharma<span className="text-teal-700">Assist</span>
          </h1>
          <p className="text-sm text-slate-600">
            Answers from FDA DailyMed labels and MedlinePlus monographs for 10 drugs, with citations.
          </p>
          <p role="note" className="mt-2 rounded-md bg-amber-50 px-3 py-1.5 text-xs text-amber-900 ring-1 ring-amber-200">
            Research and education only. Not medical advice; always confirm with a clinician or pharmacist.
          </p>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-6 px-4 py-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div>
          <div role="tablist" aria-label="Mode" className="mb-4 flex gap-1 rounded-lg bg-slate-200 p-1">
            {TABS.map((t, i) => (
              <button
                key={t.id}
                id={`tab-${t.id}`}
                role="tab"
                type="button"
                aria-selected={tab === t.id}
                aria-controls="panel"
                tabIndex={tab === t.id ? 0 : -1}
                onClick={() => setTab(t.id)}
                onKeyDown={(e) => onTabKey(e, i)}
                className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium ${
                  tab === t.id ? "bg-white text-teal-800 shadow-sm" : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          <form id="panel" role="tabpanel" aria-labelledby={`tab-${tab}`} onSubmit={submit} className="space-y-4">
            {tab === "ask" && (
              <>
                <label className="block text-sm font-medium" htmlFor="question">
                  Question
                </label>
                <textarea
                  id="question"
                  required
                  maxLength={4000}
                  rows={4}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className={input}
                  placeholder="e.g. What are the main contraindications for warfarin?"
                />
                <div>
                  <p className="mb-2 text-xs font-medium text-slate-500">Examples</p>
                  <div className="flex flex-wrap gap-2">
                    {EXAMPLES.map((q) => (
                      <button key={q} type="button" className={chip} onClick={() => setQuestion(q)}>
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
                <details className="rounded-lg border border-slate-200 bg-white p-3">
                  <summary className="cursor-pointer text-sm font-medium">
                    Patient details (optional)
                    {hasPatient && <span className="ml-2 font-normal text-teal-800">· included with the question</span>}
                  </summary>
                  <div className="mt-3">
                    <PatientForm value={patient} onChange={setPatient} />
                  </div>
                </details>
                {hasPatient && (
                  <button type="button" className={chip} onClick={() => setPatient(EMPTY_PATIENT)}>
                    Clear patient details
                  </button>
                )}
              </>
            )}

            {tab === "validate" && (
              <>
                <datalist id="corpus-drugs">
                  {CORPUS_DRUGS.map((d) => (
                    <option key={d} value={d} />
                  ))}
                </datalist>
                <fieldset className="space-y-2">
                  <legend className="mb-1 text-sm font-medium">Prescription</legend>
                  {rx.map((r, i) => (
                    <div key={i} className="grid grid-cols-[1fr_1fr_1.3fr_auto] gap-2">
                      <input aria-label={`Drug ${i + 1}`} list="corpus-drugs" required placeholder="Drug" value={r.drug} onChange={(e) => setRow(i, "drug", e.target.value)} className={input} />
                      <input aria-label={`Dose ${i + 1}`} required placeholder="500 mg" value={r.dose} onChange={(e) => setRow(i, "dose", e.target.value)} className={input} />
                      <input aria-label={`Frequency ${i + 1}`} required placeholder="twice daily" value={r.frequency} onChange={(e) => setRow(i, "frequency", e.target.value)} className={input} />
                      <button
                        type="button"
                        aria-label={`Remove drug ${i + 1}`}
                        disabled={rx.length === 1}
                        onClick={() => setRx(rx.filter((_, j) => j !== i))}
                        className="rounded-md px-2 text-slate-500 hover:bg-slate-200 disabled:opacity-30"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                  <div className="flex flex-wrap gap-2">
                    <button type="button" disabled={rx.length >= MAX_RX} onClick={() => setRx([...rx, EMPTY_RX])} className={chip}>
                      + Add drug
                    </button>
                    <button
                      type="button"
                      className={chip}
                      onClick={() => {
                        setRx([{ drug: "metformin", dose: "500 mg", frequency: "twice daily with meals" }]);
                        setPatient({ ...EMPTY_PATIENT, age: "67", sex: "male", egfr: "25", hepatic_impairment: "none" });
                      }}
                    >
                      Example: metformin at eGFR 25
                    </button>
                    <button
                      type="button"
                      className={chip}
                      onClick={() => {
                        setRx([{ drug: "sertraline", dose: "50 mg", frequency: "once daily" }]);
                        setPatient({ ...EMPTY_PATIENT, age: "58", sex: "male", egfr: "80", hepatic_impairment: "none", current_medications: "warfarin" });
                      }}
                    >
                      Example: sertraline with warfarin
                    </button>
                  </div>
                </fieldset>
              </>
            )}

            {tab === "write" && (
              <>
                <label className="block text-sm font-medium" htmlFor="description">
                  What should be prescribed?
                </label>
                <textarea
                  id="description"
                  required
                  maxLength={3500}
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className={input}
                  placeholder="e.g. First-line oral therapy for newly diagnosed type 2 diabetes"
                />
                <button
                  type="button"
                  className={chip}
                  onClick={() => {
                    setDescription("First-line oral therapy for newly diagnosed type 2 diabetes");
                    setPatient({ ...EMPTY_PATIENT, age: "60", sex: "female", egfr: "75", hepatic_impairment: "none", pregnant: "no", breastfeeding: "no" });
                  }}
                >
                  Example: type 2 diabetes
                </button>
              </>
            )}

            {showPatient && (
              <section className="rounded-lg border border-slate-200 bg-white p-3">
                <h2 className="mb-2 text-sm font-medium">Patient</h2>
                <PatientForm value={patient} onChange={setPatient} />
              </section>
            )}

            <div className="flex gap-2">
              <button
                type="submit"
                disabled={run.running}
                className="rounded-md bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-50"
              >
                {run.running ? "Working…" : tab === "ask" ? "Ask" : tab === "validate" ? "Validate" : "Draft & validate"}
              </button>
              {run.running && (
                <button type="button" onClick={cancel} className="rounded-md px-4 py-2 text-sm text-slate-700 hover:bg-slate-200">
                  Cancel
                </button>
              )}
            </div>
          </form>
        </div>

        <div className="space-y-4">
          {run.error && (
            <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-800 ring-1 ring-red-200">
              {run.error}
            </p>
          )}
          {(run.running || run.events.length > 0) && <Trace events={run.events} running={run.running} />}
          {run.result && (
            <Result
              result={run.result}
              onCite={(n) => {
                const el = document.getElementById(`src-${n}`) as HTMLDetailsElement | null;
                if (!el) return;
                el.open = true;
                el.scrollIntoView({ behavior: "smooth", block: "center" });
                el.querySelector("summary")?.focus();
              }}
            />
          )}
          {!run.running && !run.events.length && !run.error && (
            <p className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
              Ask a question, validate a prescription, or draft one. The agent plans, searches the labels, checks
              its own answer against the sources, and cites them.
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
