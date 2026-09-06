"use client";

import Link from "next/link";
import { useState } from "react";
import { verifyEvidence } from "@/lib/api";
import type { VerificationResponse } from "@/lib/types";

export default function VerifyPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<VerificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  const verify = async () => {
    if (!file || running) return;
    setRunning(true); setError(null); setResult(null);
    try { setResult(await verifyEvidence(file)); } catch (caught) { setError(caught instanceof Error ? caught.message : "Verification request failed."); } finally { setRunning(false); }
  };

  const verdict = result?.status ?? (result?.verified === true ? "VERIFIED" : result?.verified === false ? "TAMPER DETECTED" : null);
  return <main className="utility-page"><div className="utility-card"><Link href="/">&lt;- Back to dashboard</Link><p className="eyebrow">INDEPENDENT VERIFICATION</p><h1>Re-verify evidence</h1><p>Submit an evidence file to the configured backend for canonicalization, hashing, and on-chain comparison.</p><label className="file-picker">Choose evidence JSON<input type="file" accept="application/json,.json" onChange={(event) => { setFile(event.target.files?.[0] ?? null); setResult(null); }} /></label>{file && <p className="selected-file">{file.name}</p>}<button className="primary-button" disabled={!file || running} onClick={() => void verify()}>{running ? "Verifying..." : "Verify evidence"}</button>{error && <div className="error-box">{error}</div>}{result && <div className={`verification-result ${result.verified ? "success" : "danger"}`}><strong>{verdict ?? "Verification response"}</strong><span>{result.reason ?? "The backend returned a verification response."}</span><pre className="json-viewer">{JSON.stringify(result, null, 2)}</pre></div>}</div></main>;
}
