import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TraceChain AI | Evidence intelligence",
  description: "Authorized face discovery and blockchain evidence verification."
};

const themeInitScript = `
(function () {
  try {
    var stored = localStorage.getItem("tracechain-theme");
    var theme = stored === "light" || stored === "dark" ? stored : "dark";
    document.documentElement.setAttribute("data-theme", theme);
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="dark">
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>
        <div className="page">
          <div className="grain" aria-hidden="true" />
          {children}
        </div>
      </body>
    </html>
  );
}
