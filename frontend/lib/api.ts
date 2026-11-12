// Types mirror backend/pharma_assist/schemas.py; the client streams POST /ask/stream (SSE over fetch,
// since EventSource cannot POST).

export type Patient = {
  age?: number;
  sex?: "female" | "male";
  weight_kg?: number;
  egfr?: number;
  hepatic_impairment?: "none" | "mild" | "moderate" | "severe";
  pregnant?: boolean;
  breastfeeding?: boolean;
  conditions?: string[];
  allergies?: string[];
  current_medications?: string[];
};

export type Source = {
  id: string;
  file: string;
  drug: string | null;
  heading: string;
  section: string;
  url: string | null;
  text: string;
};

export type Verdict = "approved" | "approved_with_warnings" | "needs_more_info" | "rejected";
export type Severity = "critical" | "major" | "minor";

export type Issue = {
  severity: Severity;
  category: string;
  drug: string | null;
  message: string;
  source_ids: string[];
};

export type ValidationReport = { verdict: Verdict; issues: Issue[]; summary: string };

export type PrescriptionItem = {
  drug: string;
  dose: string;
  route: string;
  frequency: string;
  duration?: string | null;
  indication?: string | null;
};

export type Draft = { items: PrescriptionItem[]; rationale: string; source_ids: string[] };

export type Critique = {
  verdict: "approve" | "revise";
  unsupported_claims: string[];
  ambiguities: string[];
  feedback: string;
};

export type AskResponse = {
  answer: string;
  citations: Source[]; // citations[n - 1] is the passage behind [n]
  plan: string[];
  review: Critique | null;
  revisions: number;
  validation: ValidationReport | null;
  draft: Draft | null;
};

export type TraceEvent =
  | { event: "plan"; data: { steps: string[] } }
  | { event: "tool_call"; data: { calls: { name: string; args: Record<string, unknown> }[] } }
  | {
      event: "tool_result";
      data: { name: string; status: string; source_ids: string[]; verdict: Verdict | null };
    }
  | { event: "review"; data: Critique & { revising: boolean } }
  | { event: "final"; data: AskResponse }
  | { event: "error"; data: { message: string } };

// `next dev` runs on :3000 next to `uvicorn` on :8000; the exported build is served by the API itself.
const API = process.env.NODE_ENV === "development" ? "http://localhost:8000" : "";

async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (Array.isArray(body.detail)) {
      // FastAPI 422: [{loc: ["body", "patient", "egfr"], msg: "..."}]
      return body.detail
        .map((d: { loc: string[]; msg: string }) => `${d.loc.slice(1).join(".")}: ${d.msg}`)
        .join("; ");
    }
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // not JSON
  }
  return `Request failed (HTTP ${res.status}).`;
}

export async function streamAsk(
  body: { question: string; patient: Patient | null; images: string[] },
  onEvent: (e: TraceEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API}/ask/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(await errorMessage(res));

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  let finished = false;
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value.replace(/\r\n/g, "\n");
    let end;
    while ((end = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      let event = "";
      let data = "";
      for (const line of block.split("\n")) {
        if (line.startsWith("event: ")) event = line.slice(7);
        else if (line.startsWith("data: ")) data += line.slice(6);
      }
      if (!event || !data) continue; // keep-alive comment
      const parsed = { event, data: JSON.parse(data) } as TraceEvent;
      finished ||= event === "final" || event === "error";
      onEvent(parsed);
    }
  }
  if (!finished) throw new Error("The connection closed before the answer was ready. Please retry.");
}
