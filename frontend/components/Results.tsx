import type { AskResponse, Critique, Draft, Severity, Source, TraceEvent, ValidationReport, Verdict } from "@/lib/api";
import { Icon, type ICONS } from "./Icons";
import { Markdown } from "./Markdown";

type Cite = (n: number) => void;
type IconName = keyof typeof ICONS;

const card = "rounded-2xl border border-slate-200 bg-white shadow-sm";

// --- verdicts ----------------------------------------------------------------------------------

const VERDICT: Record<Verdict, { label: string; icon: IconName; banner: string; badge: string; iconTone: string }> = {
  approved: {
    label: "Approved",
    icon: "checkCircle",
    banner: "border-emerald-200 bg-emerald-50",
    badge: "bg-emerald-100 text-emerald-800 ring-emerald-200",
    iconTone: "text-emerald-600",
  },
  approved_with_warnings: {
    label: "Approved with warnings",
    icon: "warning",
    banner: "border-amber-200 bg-amber-50",
    badge: "bg-amber-100 text-amber-900 ring-amber-200",
    iconTone: "text-amber-600",
  },
  needs_more_info: {
    label: "Needs more information",
    icon: "info",
    banner: "border-sky-200 bg-sky-50",
    badge: "bg-sky-100 text-sky-900 ring-sky-200",
    iconTone: "text-sky-600",
  },
  rejected: {
    label: "Rejected",
    icon: "xCircle",
    banner: "border-red-200 bg-red-50",
    badge: "bg-red-100 text-red-800 ring-red-200",
    iconTone: "text-red-600",
  },
};

const SEVERITY: Record<Severity, string> = {
  critical: "bg-red-600 text-white",
  major: "bg-amber-400 text-amber-950",
  minor: "bg-slate-200 text-slate-700",
};

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const v = VERDICT[verdict];
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ${v.badge}`}>
      {v.label}
    </span>
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
        className="ml-1 rounded-md bg-teal-50 px-1.5 text-[0.7rem] font-semibold text-teal-800 ring-1 ring-teal-200 hover:bg-teal-100"
        aria-label={`Show source ${n}`}
      >
        {n}
      </button>
    ) : (
      <span key={id} className="ml-1 font-mono text-[0.7rem] text-slate-400">
        {id}
      </span>
    );
  });
}

function VerdictBanner({ report, citations, onCite }: { report: ValidationReport; citations: Source[]; onCite: Cite }) {
  const v = VERDICT[report.verdict];
  return (
    <section aria-labelledby="verdict-title" className={`rounded-2xl border p-5 shadow-sm ${v.banner}`}>
      <div className="flex items-start gap-3">
        <Icon name={v.icon} className={`h-8 w-8 shrink-0 ${v.iconTone}`} />
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Prescription check</p>
          <h2 id="verdict-title" className="text-xl font-semibold text-slate-900">
            {v.label}
          </h2>
          <p className="mt-1 text-sm text-slate-700">{report.summary}</p>
        </div>
      </div>
      {report.issues.length > 0 && (
        <ul className="mt-4 space-y-2">
          {report.issues.map((issue, i) => (
            <li key={i} className="flex gap-3 rounded-xl bg-white/80 p-3 text-sm ring-1 ring-black/5">
              <span className={`h-fit shrink-0 rounded-md px-1.5 py-0.5 text-[0.65rem] font-bold uppercase ${SEVERITY[issue.severity]}`}>
                {issue.severity}
              </span>
              <span className="min-w-0 text-slate-700">
                <span className="font-medium text-slate-900">
                  {issue.category.replace(/_/g, " ")}
                  {issue.drug ? ` · ${issue.drug}` : ""}
                </span>
                {" — "}
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

// --- agent trace (timeline) --------------------------------------------------------------------

type ToolResult = { status: string; passages: number; verdict: Verdict | null };
type Step =
  | { kind: "plan"; steps: string[] }
  | { kind: "tool"; name: string; args: Record<string, unknown>; result?: ToolResult }
  | { kind: "review"; review: Critique & { revising: boolean } }
  | { kind: "done" };

/** Events -> timeline steps; each tool result is attached to the oldest pending call of that tool. */
function toSteps(events: TraceEvent[]): Step[] {
  const steps: Step[] = [];
  for (const e of events) {
    if (e.event === "plan") steps.push({ kind: "plan", steps: e.data.steps });
    else if (e.event === "tool_call") for (const c of e.data.calls) steps.push({ kind: "tool", ...c });
    else if (e.event === "tool_result") {
      const call = steps.find((s): s is Extract<Step, { kind: "tool" }> => s.kind === "tool" && s.name === e.data.name && !s.result);
      if (call) call.result = { status: e.data.status, passages: e.data.source_ids.length, verdict: e.data.verdict };
    } else if (e.event === "review") steps.push({ kind: "review", review: e.data });
    else if (e.event === "final") steps.push({ kind: "done" });
  }
  return steps;
}

const TOOL: Record<string, { title: string; icon: IconName }> = {
  build_context: { title: "Searched the drug labels", icon: "search" },
  validate_prescription: { title: "Checked the prescription", icon: "shield" },
  write_prescription: { title: "Drafted a prescription", icon: "pencil" },
};

function toolDetail(name: string, args: Record<string, unknown>): string {
  if (name === "build_context") {
    const filters = [args.drugs, args.sections]
      .filter((f): f is string[] => Array.isArray(f) && f.length > 0)
      .map((f) => f.join(", "));
    return `“${String(args.query ?? "")}”${filters.length ? ` · ${filters.join(" · ")}` : ""}`;
  }
  if (name === "validate_prescription") {
    const items = Array.isArray(args.prescription) ? (args.prescription as { drug?: string; dose?: string; frequency?: string }[]) : [];
    return items.map((i) => [i.drug, i.dose, i.frequency].filter(Boolean).join(" ")).join("; ");
  }
  if (name === "write_prescription") return `“${String(args.description ?? "")}”`;
  return "";
}

function Spinner() {
  return <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" aria-hidden />;
}

function TimelineItem({ icon, tone, title, children }: { icon: IconName; tone: string; title: React.ReactNode; children?: React.ReactNode }) {
  return (
    <li className="relative flex gap-3">
      <span className={`z-10 grid h-8 w-8 shrink-0 place-items-center rounded-full ring-4 ring-white ${tone}`}>
        <Icon name={icon} className="h-4 w-4" />
      </span>
      <div className="min-w-0 pt-1.5 text-sm">
        <p className="font-medium text-slate-900">{title}</p>
        {children && <div className="mt-0.5 text-slate-600">{children}</div>}
      </div>
    </li>
  );
}

function stepView(s: Step, i: number) {
  switch (s.kind) {
    case "plan":
      return (
        <TimelineItem key={i} icon="list" tone="bg-slate-100 text-slate-600" title="Planned the answer">
          <ol className="list-decimal space-y-0.5 pl-4">
            {s.steps.map((p, j) => (
              <li key={j}>{p}</li>
            ))}
          </ol>
        </TimelineItem>
      );
    case "tool": {
      const t = TOOL[s.name] ?? { title: s.name, icon: "sparkles" as const };
      return (
        <TimelineItem
          key={i}
          icon={t.icon}
          tone="bg-teal-50 text-teal-700"
          title={
            <span className="flex flex-wrap items-center gap-2">
              {t.title}
              <code className="rounded bg-slate-100 px-1.5 py-0.5 text-[0.7rem] font-normal text-slate-500">{s.name}</code>
            </span>
          }
        >
          <p className="break-words">{toolDetail(s.name, s.args)}</p>
          <p className="mt-1 flex items-center gap-2 text-xs text-slate-500">
            {!s.result ? (
              <>
                <Spinner /> running…
              </>
            ) : s.result.status === "error" ? (
              <span className="text-red-700">failed; the agent adapts</span>
            ) : (
              <>
                {s.result.passages} passage{s.result.passages === 1 ? "" : "s"}
                {s.result.verdict && <VerdictBadge verdict={s.result.verdict} />}
              </>
            )}
          </p>
        </TimelineItem>
      );
    }
    case "review": {
      const r = s.review;
      const ok = r.verdict === "approve";
      return (
        <TimelineItem
          key={i}
          icon="shield"
          tone={ok ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}
          title={ok ? "Critic: every claim is backed by a source" : r.revising ? "Critic asked for a revision" : "Critic flagged claims it could not verify"}
        >
          {!ok && (
            <p>
              {r.unsupported_claims.length} unsupported claim{r.unsupported_claims.length === 1 ? "" : "s"}
              {r.revising ? " — the agent is revising its answer." : " — listed under Reviewer notes."}
            </p>
          )}
        </TimelineItem>
      );
    }
    case "done":
      return <TimelineItem key={i} icon="check" tone="bg-emerald-600 text-white" title="Answer ready" />;
  }
}

export function Trace({ events, running, seconds }: { events: TraceEvent[]; running: boolean; seconds: number }) {
  return (
    <section aria-labelledby="trace-title" className={`${card} p-5`}>
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 id="trace-title" className="text-sm font-semibold text-slate-900">
          Agent trace
        </h2>
        <span className="flex items-center gap-2 text-xs text-slate-500" aria-live="off">
          {running ? (
            <>
              <Spinner /> Working · {seconds} s
            </>
          ) : (
            `${seconds} s`
          )}
        </span>
      </div>
      <ol
        aria-live="polite"
        className="relative space-y-4 before:absolute before:bottom-2 before:left-[15px] before:top-2 before:w-px before:bg-slate-200"
      >
        {toSteps(events).map(stepView)}
        {running && (
          <li className="relative flex items-center gap-3 text-sm text-slate-500">
            <span className="z-10 grid h-8 w-8 place-items-center rounded-full bg-white ring-4 ring-white">
              <Spinner />
            </span>
            Thinking… prescription checks can take a minute.
          </li>
        )}
      </ol>
    </section>
  );
}

// --- answer, draft, passages -------------------------------------------------------------------

function DraftCard({ draft }: { draft: Draft }) {
  return (
    <section aria-labelledby="draft-title" className={`${card} p-5`}>
      <h2 id="draft-title" className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900">
        <Icon name="pencil" className="h-4 w-4 text-teal-700" /> Drafted prescription
      </h2>
      {draft.items.length ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="pb-2 pr-4 font-medium">Drug</th>
                <th className="pb-2 pr-4 font-medium">Dose</th>
                <th className="pb-2 pr-4 font-medium">Route</th>
                <th className="pb-2 pr-4 font-medium">Frequency</th>
                <th className="pb-2 font-medium">Duration</th>
              </tr>
            </thead>
            <tbody>
              {draft.items.map((it, i) => (
                <tr key={i} className="border-t border-slate-100">
                  <td className="py-2 pr-4 font-semibold text-slate-900">{it.drug}</td>
                  <td className="py-2 pr-4">{it.dose}</td>
                  <td className="py-2 pr-4">{it.route}</td>
                  <td className="py-2 pr-4">{it.frequency}</td>
                  <td className="py-2">{it.duration ?? "—"}</td>
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
    <section aria-labelledby="passages-title" className={`${card} p-5`}>
      <h2 id="passages-title" className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900">
        <Icon name="document" className="h-4 w-4 text-teal-700" /> Cited passages
      </h2>
      <div className="space-y-2">
        {citations.map((s, i) => (
          <details key={s.id} id={`src-${i + 1}`} className="group rounded-xl border border-slate-200 open:border-teal-200 open:bg-teal-50/40">
            <summary className="flex cursor-pointer list-none items-start gap-3 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-600">
              <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-teal-600 text-xs font-bold text-white">{i + 1}</span>
              <span className="min-w-0 flex-1">
                <span className="block font-medium text-slate-900">{s.file}</span>
                <span className="block text-xs text-slate-500">{s.heading}</span>
              </span>
              <Icon name="chevron" className="mt-1 h-4 w-4 shrink-0 text-slate-400 transition-transform group-open:rotate-90" />
            </summary>
            <div className="px-3 pb-3 pl-12 text-sm">
              <p className="whitespace-pre-line text-slate-700">{s.text}</p>
              {s.url && (
                <a
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-teal-700 hover:underline"
                >
                  Open the original label <Icon name="external" className="h-3.5 w-3.5" />
                </a>
              )}
            </div>
          </details>
        ))}
      </div>
    </section>
  );
}

/**
 * Splits the finalizer's answer (`agent.finalizer`: body, **Reviewer notes**, **Sources**, *Disclaimer*) so each
 * part gets its own styling. If the markers are missing, everything stays in `body`, so nothing is lost.
 */
function splitAnswer(answer: string) {
  const cut = (text: string, marker: string): [string, string] => {
    const at = text.lastIndexOf(marker);
    return at < 0 ? [text, ""] : [text.slice(0, at), text.slice(at + marker.length)];
  };
  const [beforeDisclaimer, disclaimer] = cut(answer, "\n\n*Disclaimer: ");
  const [beforeSources, sources] = cut(beforeDisclaimer, "\n\n**Sources**\n");
  const [body, notes] = cut(beforeSources, "\n\n**Reviewer notes**\n");
  return { body, notes, sources, disclaimer: disclaimer.replace(/\*\s*$/, "") };
}

export function Result({ result, onCite }: { result: AskResponse; onCite: Cite }) {
  const approved = result.review?.verdict === "approve";
  const { body, notes, sources, disclaimer } = splitAnswer(result.answer);
  return (
    <>
      {result.validation && <VerdictBanner report={result.validation} citations={result.citations} onCite={onCite} />}
      {result.draft && <DraftCard draft={result.draft} />}
      <section aria-labelledby="answer-title" className={`${card} p-6`}>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 id="answer-title" className="text-sm font-semibold text-slate-900">
            Answer
          </h2>
          {result.review && (
            <span
              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ${
                approved ? "bg-emerald-50 text-emerald-800 ring-emerald-200" : "bg-amber-50 text-amber-900 ring-amber-200"
              }`}
            >
              <Icon name="shield" className="h-3.5 w-3.5" />
              {approved ? "Checked against sources" : "Some claims unverified"}
            </span>
          )}
        </div>
        <Markdown text={body} onCite={onCite} />
        {notes && (
          <div className="mt-5 rounded-xl bg-amber-50 p-4 ring-1 ring-amber-200">
            <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-amber-900">
              <Icon name="warning" className="h-4 w-4" /> Reviewer notes
            </p>
            <div className="text-sm">
              <Markdown text={notes} onCite={onCite} />
            </div>
          </div>
        )}
        {/* The cited-passages card below lists the sources in detail; keep the text list only when it is empty. */}
        {sources && !result.citations.length && (
          <p className="mt-5 text-sm font-medium text-slate-600">{sources.trim()}</p>
        )}
        {disclaimer && (
          <p className="mt-5 flex gap-2 border-t border-slate-100 pt-4 text-xs text-slate-500">
            <Icon name="info" className="h-4 w-4 shrink-0" />
            {disclaimer}
          </p>
        )}
      </section>
      <Passages citations={result.citations} />
    </>
  );
}
