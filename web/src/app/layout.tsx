import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Civic Inspection Lab | Policy Lab",
  description: "Explore transparent tradeoffs in equitable inspection triage.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
