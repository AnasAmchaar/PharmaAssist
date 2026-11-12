"use client";

import { useRef, useState, type FormEvent } from "react";
import { EMPTY_PATIENT, PatientForm, input, toPatient, type PatientFields } from "@/components/PatientForm";
import { Result, Trace } from "@/components/Results";
import { streamAsk, type AskResponse, type TraceEvent } from "@/lib/api";

// One request box: the agent decides from the wording whether to search the labels, validate a
// prescription or draft one. Examples are plain language with no hint about which tool to use.
type Example = { label: string; question: string; patient?: Partial<PatientFields> };
const EXAMPLES: { group: string; items: Example[] }[] = [
  {
    group: "Questions (the four public evaluation questions)",
    items: [
      { label: "Warfarin contraindications", question: "What are the main contraindications for warfarin?" },
      {
        label: "Warfarin vs apixaban",
        question:
          "Compare the contraindications of warfarin and apixaban. What conditions are shared and which are unique to each drug?",
      },
      {
        label: "Warfarin + sertraline bleeding risk",
        question:
          "A patient currently on warfarin is prescribed sertraline. What is the risk of bleeding and what monitoring is recommended?",
      },
      {
        label: "Metformin at eGFR 25",
        question:
          "A patient with an eGFR of 25 mL/min is being considered for metformin. Is metformin contraindicated at this level of renal function, and what is the threshold?",
      },
    ],
  },
  {
    group: "Is this prescription safe for my patient?",
    items: [
      {
        label: "Metformin, kidney disease",
        question: "Can I start my patient on metformin 500 mg twice daily?",
        patient: { age: "67", sex: "male", egfr: "25", hepatic_impairment: "none" },
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
    items: [
      {
        label: "New type 2 diabetes",
        question: "What should I prescribe this patient for newly diagnosed type 2 diabetes?",
        patient: {
          age: "60",
          sex: "female",
          egfr: "75",
          hepatic_impairment: "none",
          pregnant: "no",
          breastfeeding: "no",
        },
      },
    ],
  },
];

type Run = { events: TraceEvent[]; result: AskResponse | null; error: string | null; running: boolean };
const IDLE: Run = { events: [], result: null, error: null, running: false };

const chip =
  "rounded-full border border-slate-300 bg-white px-3 py-1 text-left text-xs text-slate-700 hover:border-teal-600 hover:text-teal-800";

export default function Home() {
  const [question, setQuestion] = useState("");
  const [patient, setPatient] = useState<PatientFields>(EMPTY_PATIENT);
  const [patientOpen, setPatientOpen] = useState(false);
  const [run, setRun] = useState<Run>(IDLE);
  const abort = useRef<AbortController | null>(null);
  const hasPatient = toPatient(patient) !== null;

  async function submit(e: FormEvent) {
    e.preventDefault();
    abort.current?.abort();
    const ctrl = new AbortController();
    abort.current = ctrl;
    setRun({ ...IDLE, running: true });
    const update = (fn: (r: Run) => Run) => {
      if (abort.current === ctrl) setRun(fn); // ignore events from a superseded run
    };
    try {
      await streamAsk(
        { question: question.trim(), patient: toPatient(patient) },
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
      update((r) => ({ ...r, running: false }));
    }
  }

  function cancel() {
    abort.current?.abort();
    abort.current = null;
    setRun((r) => ({ ...r, running: false, error: "Cancelled." }));
  }

  function loadExample(ex: Example) {
    setQuestion(ex.question);
    // Each example brings its own patient (or none), so details from an earlier example never leak in.
    setPatient({ ...EMPTY_PATIENT, ...ex.patient });
    setPatientOpen(Boolean(ex.patient));
  }

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
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium" htmlFor="question">
              Your request
            </label>
            <textarea
              id="question"
              required
              maxLength={4000}
              rows={5}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className={input}
              aria-describedby="question-hint"
              placeholder="Ask about a drug, check whether a prescription is safe for your patient, or ask what to prescribe."
            />
            <p id="question-hint" className="mt-1 text-xs text-slate-500">
              The agent decides how to handle it: search the labels, check a prescription, or draft one.
            </p>
          </div>

          <details
            open={patientOpen}
            onToggle={(e) => setPatientOpen(e.currentTarget.open)}
            className="rounded-lg border border-slate-200 bg-white p-3"
          >
            <summary className="cursor-pointer text-sm font-medium">
              Patient details (optional)
              {hasPatient && <span className="ml-2 font-normal text-teal-800">· included with the request</span>}
            </summary>
            <div className="mt-3 space-y-3">
              <PatientForm value={patient} onChange={setPatient} />
              {hasPatient && (
                <button type="button" className={chip} onClick={() => setPatient(EMPTY_PATIENT)}>
                  Clear patient details
                </button>
              )}
            </div>
          </details>

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={run.running}
              className="rounded-md bg-teal-700 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-50"
            >
              {run.running ? "Working…" : "Ask"}
            </button>
            {run.running && (
              <button type="button" onClick={cancel} className="rounded-md px-4 py-2 text-sm text-slate-700 hover:bg-slate-200">
                Cancel
              </button>
            )}
          </div>

          <section aria-labelledby="examples-title" className="space-y-3">
            <h2 id="examples-title" className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Examples
            </h2>
            {EXAMPLES.map((g) => (
              <div key={g.group}>
                <p className="mb-1.5 text-xs font-medium text-slate-600">{g.group}</p>
                <div className="flex flex-wrap gap-2">
                  {g.items.map((ex) => (
                    <button key={ex.label} type="button" className={chip} title={ex.question} onClick={() => loadExample(ex)}>
                      {ex.label}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </section>
        </form>

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
              The agent plans, chooses its tools (label search, prescription check, prescription draft), checks its
              own answer against the sources, and cites them. Its steps appear here as it works.
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
