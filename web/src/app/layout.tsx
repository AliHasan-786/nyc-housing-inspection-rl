import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Civic Inspection Lab | Frozen Policy Explorer",
  description: "Inspect corrected, artifact-backed NYC inspection-triage policy tradeoffs.",
  openGraph: {
    title: "Civic Inspection Lab | Frozen Policy Explorer",
    description: "A static, artifact-backed civic-AI policy laboratory.",
    type: "website",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
