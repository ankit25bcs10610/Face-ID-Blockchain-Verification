"use client";

import Link from "next/link";
import { useState } from "react";

export default function EvidencePage() {
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const readEvidence = async (file: File | undefined) => {
    if (!file) return;
    setError(null);
    try {
      const parsed = JSON.parse(await file.text());
      setContent(JSON.stringify(parsed, null, 2));
    } catch {
      setContent(null);
      setError("Choose a valid evidence JSON file.");
    }
  };

  return <main className="utility-page"><div className="utility-card"><Link href="/">&lt;- Back to dashboard</Link><p className="eyebrow">EVIDENCE EXPLORER</p><h1>Inspect canonical evidence</h1><p>Select an evidence JSON file to inspect the exact structured record. No data is generated in this view.</p><label className="file-picker">Choose evidence JSON<input type="file" accept="application/json,.json" onChange={(event) => void readEvidence(event.target.files?.[0])} /></label>{error && <div className="error-box">{error}</div>}{content && <pre className="json-viewer">{content}</pre>}</div></main>;
}
