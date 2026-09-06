import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TraceChain AI | Evidence intelligence",
  description: "Authorized face discovery and blockchain evidence verification."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
