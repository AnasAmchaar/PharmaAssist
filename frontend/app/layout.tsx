import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PharmaAssist",
  description: "Agentic pharmacology research assistant over FDA DailyMed and MedlinePlus drug labels",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
