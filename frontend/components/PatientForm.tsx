import type { Patient } from "@/lib/api";

// Form state is kept as strings; empty means "unknown" and is omitted, so the backend treats it as
// unknown (not normal) and the validator can ask for it.
export type PatientFields = {
  age: string;
  sex: string;
  weight_kg: string;
  egfr: string;
  hepatic_impairment: string;
  pregnant: string;
  breastfeeding: string;
  conditions: string;
  allergies: string;
  current_medications: string;
};

export const EMPTY_PATIENT: PatientFields = {
  age: "",
  sex: "",
  weight_kg: "",
  egfr: "",
  hepatic_impairment: "",
  pregnant: "",
  breastfeeding: "",
  conditions: "",
  allergies: "",
  current_medications: "",
};

const list = (s: string) =>
  s
    .split(/[,;\n]/)
    .map((x) => x.trim())
    .filter(Boolean); // the API rejects blank entries

/** null when nothing is filled in, so plain questions are sent without a patient. */
export function toPatient(f: PatientFields): Patient | null {
  const p: Patient = {};
  if (f.age) p.age = Number(f.age);
  if (f.sex) p.sex = f.sex as Patient["sex"];
  if (f.weight_kg) p.weight_kg = Number(f.weight_kg);
  if (f.egfr) p.egfr = Number(f.egfr);
  if (f.hepatic_impairment) p.hepatic_impairment = f.hepatic_impairment as Patient["hepatic_impairment"];
  if (f.pregnant) p.pregnant = f.pregnant === "yes";
  if (f.breastfeeding) p.breastfeeding = f.breastfeeding === "yes";
  for (const key of ["conditions", "allergies", "current_medications"] as const) {
    const items = list(f[key]);
    if (items.length) p[key] = items;
  }
  return Object.keys(p).length ? p : null;
}

export const input =
  "w-full rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm focus:border-teal-600 focus:outline-none focus:ring-1 focus:ring-teal-600";

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-slate-700">
        {label} {hint && <span className="font-normal text-slate-500">{hint}</span>}
      </span>
      {children}
    </label>
  );
}

function Choice({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: [string, string][];
}) {
  return (
    <select className={input} value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">Unknown</option>
      {options.map(([v, label]) => (
        <option key={v} value={v}>
          {label}
        </option>
      ))}
    </select>
  );
}

export function PatientForm({ value, onChange }: { value: PatientFields; onChange: (v: PatientFields) => void }) {
  const set = (key: keyof PatientFields) => (v: string) => onChange({ ...value, [key]: v });
  const yesNo: [string, string][] = [
    ["no", "No"],
    ["yes", "Yes"],
  ];
  return (
    <fieldset className="space-y-3">
      <legend className="sr-only">Patient details</legend>
      <p className="text-xs text-slate-500">Leave a field empty if unknown. Unknown is not treated as normal.</p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Field label="Age" hint="years">
          <input className={input} type="number" min={0} max={120} value={value.age} onChange={(e) => set("age")(e.target.value)} />
        </Field>
        <Field label="Sex">
          <Choice value={value.sex} onChange={set("sex")} options={[["female", "Female"], ["male", "Male"]]} />
        </Field>
        <Field label="Weight" hint="kg">
          <input className={input} type="number" min={1} max={400} step="any" value={value.weight_kg} onChange={(e) => set("weight_kg")(e.target.value)} />
        </Field>
        <Field label="eGFR" hint="mL/min/1.73 m²">
          <input className={input} type="number" min={0} max={200} step="any" value={value.egfr} onChange={(e) => set("egfr")(e.target.value)} />
        </Field>
        <Field label="Hepatic impairment">
          <Choice
            value={value.hepatic_impairment}
            onChange={set("hepatic_impairment")}
            options={[["none", "None"], ["mild", "Mild"], ["moderate", "Moderate"], ["severe", "Severe"]]}
          />
        </Field>
        <Field label="Pregnant">
          <Choice value={value.pregnant} onChange={set("pregnant")} options={yesNo} />
        </Field>
        <Field label="Breastfeeding">
          <Choice value={value.breastfeeding} onChange={set("breastfeeding")} options={yesNo} />
        </Field>
      </div>
      <Field label="Conditions" hint="comma-separated">
        <input className={input} value={value.conditions} onChange={(e) => set("conditions")(e.target.value)} placeholder="e.g. atrial fibrillation, peptic ulcer" />
      </Field>
      <Field label="Allergies" hint="comma-separated">
        <input className={input} value={value.allergies} onChange={(e) => set("allergies")(e.target.value)} placeholder="e.g. penicillin" />
      </Field>
      <Field label="Current medications" hint="generic names, comma-separated">
        <input className={input} value={value.current_medications} onChange={(e) => set("current_medications")(e.target.value)} placeholder="e.g. warfarin" />
      </Field>
    </fieldset>
  );
}
