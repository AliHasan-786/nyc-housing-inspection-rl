import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Civic Inspection Lab | Frozen Policy Explorer",
  description: "Compare corrected NYC inspection-triage policy results from a frozen simulator benchmark.",
  openGraph: {
    title: "Civic Inspection Lab | Frozen Policy Explorer",
    description: "A static explorer for corrected NYC inspection-triage benchmark results.",
    type: "website",
    images: [{ url: "https://raw.githubusercontent.com/AliHasan-786/nyc-housing-inspection-rl/main/web/public/og-civic-inspection-lab.svg", width: 1200, height: 630 }],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
