import { Fragment, type ReactNode } from "react";

// Renders the small markdown subset the agent writes (headings, bullet/numbered lists, tables, **bold**,
// *italic*) as React elements, with [n] citations as buttons. No HTML injection: text stays text.

const INLINE = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*|\[\d+\])/g;
const LIST = /^(\s*)([-*]|\d+\.)\s+(.*)$/;
const TABLE_SEPARATOR = /^\s*\|[\s:|-]+\|\s*$/;

type Cite = (n: number) => void;

function inline(text: string, onCite: Cite): ReactNode[] {
  return text.split(INLINE).map((part, i) => {
    if (part.length > 4 && part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{inline(part.slice(2, -2), onCite)}</strong>;
    }
    if (/^\[\d+\]$/.test(part)) {
      const n = Number(part.slice(1, -1));
      return (
        <button
          key={i}
          type="button"
          onClick={() => onCite(n)}
          aria-label={`Show source ${n}`}
          className="mx-0.5 rounded-md bg-teal-50 px-1.5 align-super text-[0.68rem] font-semibold text-teal-800 ring-1 ring-teal-200 hover:bg-teal-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-600"
        >
          {n}
        </button>
      );
    }
    if (part.length > 2 && part.startsWith("*") && part.endsWith("*")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

function cells(row: string): string[] {
  return row
    .trim()
    .replace(/^\||\|$/g, "")
    .split("|")
    .map((c) => c.trim());
}

export function Markdown({ text, onCite }: { text: string; onCite: Cite }) {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;
  while (i < lines.length) {
    const start = i;
    const line = lines[i];
    if (!line.trim()) {
      i++;
      continue;
    }
    const heading = /^#{1,6}\s+(.*)$/.exec(line);
    if (heading) {
      blocks.push(
        <h3 key={start} className="mt-4 font-semibold text-slate-900">
          {inline(heading[1], onCite)}
        </h3>,
      );
      i++;
    } else if (LIST.test(line)) {
      const items: ReactNode[] = [];
      for (; i < lines.length && LIST.test(lines[i]); i++) {
        const [, indent, , content] = LIST.exec(lines[i])!;
        items.push(
          <li key={i} className={indent ? "ml-5" : undefined}>
            {inline(content, onCite)}
          </li>,
        );
      }
      blocks.push(
        /^\s*\d+\./.test(line) ? (
          <ol key={start} className="list-decimal space-y-1 pl-6">
            {items}
          </ol>
        ) : (
          <ul key={start} className="list-disc space-y-1 pl-6">
            {items}
          </ul>
        ),
      );
    } else if (line.trim().startsWith("|")) {
      const rows: string[][] = [];
      for (; i < lines.length && lines[i].trim().startsWith("|"); i++) {
        if (!TABLE_SEPARATOR.test(lines[i])) rows.push(cells(lines[i]));
      }
      const [head = [], ...body] = rows;
      blocks.push(
        <div key={start} className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-sm">
            <thead>
              <tr>
                {head.map((c, j) => (
                  <th key={j} className="border-b border-slate-300 px-2 py-1 font-semibold">
                    {inline(c, onCite)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {body.map((r, k) => (
                <tr key={k} className="border-b border-slate-100 align-top">
                  {r.map((c, j) => (
                    <td key={j} className="px-2 py-1">
                      {inline(c, onCite)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
    } else {
      const para: string[] = [];
      for (; i < lines.length && lines[i].trim(); i++) {
        if (i > start && (LIST.test(lines[i]) || /^(#{1,6}\s|\s*\|)/.test(lines[i]))) break;
        para.push(lines[i]);
      }
      blocks.push(
        <p key={start}>
          {para.map((l, j) => (
            <Fragment key={j}>
              {j > 0 && <br />}
              {inline(l, onCite)}
            </Fragment>
          ))}
        </p>,
      );
    }
  }
  return <div className="space-y-3 leading-relaxed text-slate-800">{blocks}</div>;
}
