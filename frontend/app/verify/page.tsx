"use client";

import { Check, CircleAlert, FileJson, Hash, LoaderCircle, Link2, Search, ShieldCheck, TriangleAlert, Upload } from "lucide-react";
import { useState } from "react";
import SiteNav from "@/components/site-nav";
import { verifyEvidence } from "@/lib/api";
import type { VerificationResponse } from "@/lib/types";

const STEPS = [
  { icon: FileJson, label: "Parse evidence" },
  { icon: Search, label: "Canonicalize JSON" },
  { icon: Hash, label: "Recalculate SHA-256" },
  { icon: Link2, label: "Fetch on-chain record" },
  { icon: ShieldCheck, label: "Compare hashes" }
];

function show(value: unknown) {
  return value === undefined || value === null || value === "" ? "—" : String(value);
}

export default function VerifyPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<VerificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [dragging, setDragging] = useState(false);

  const verify = async () => {
    if (!file || running) return;
    setRunning(true); setError(null); setResult(null);
    try {
      setResult(await verifyEvidence(file));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Verification request failed.");
    } finally {
      setRunning(false);
    }
  };

  const verified = result?.verified === true;
  const verdict = result?.status ?? (verified ? "VERIFIED" : result ? "TAMPER DETECTED" : null);

  return (
    <main>
      <SiteNav />

      <section className="verify-head">
        <div>
          <p className="kicker">Independent cryptographic verification</p>
          <h1>Verify evidence integrity</h1>
          <p className="lede">
            Submit an ORYNEX AI evidence record. The backend canonicalizes it, recalculates its SHA-256
            fingerprint, reads the commitment stored on-chain, and compares the two.
          </p>
        </div>
      </section>

      <section className="verify-steps">
        {STEPS.map((step, index) => (
          <div className="verify-step" key={step.label}>
            <span className="step-icon"><step.icon size={16} /></span>
            <span className="step-label">{step.label}</span>
            {index < STEPS.length - 1 && <span className="step-arrow">→</span>}
          </div>
        ))}
      </section>

      <section className="verify-body">
        <div className="verify-upload">
          <div className="col-head"><div><span className="idx">01</span><h2>Evidence record</h2></div></div>
          <label
            className={`dropzone compact ${dragging ? "dragging" : ""}`}
            onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={(event) => {
              event.preventDefault(); setDragging(false);
              const dropped = event.dataTransfer.files?.[0];
              if (dropped) { setFile(dropped); setResult(null); setError(null); }
            }}
          >
            <Upload className="icon" size={24} />
            <strong>{file ? file.name : "Drop your evidence JSON here"}</strong>
            <span>{file ? `${(file.size / 1024).toFixed(1)} KB` : "or click to browse"}</span>
            <input
              type="file"
              accept="application/json,.json"
              hidden
              onChange={(event) => { setFile(event.target.files?.[0] ?? null); setResult(null); setError(null); }}
            />
          </label>
          <button className="run-btn" disabled={!file || running} onClick={() => void verify()}>
            {running ? <><LoaderCircle className="spin" size={16} /> Verifying…</> : <><ShieldCheck size={16} /> Verify integrity</>}
          </button>
          {error && <div className="error-line"><CircleAlert size={15} /><span>{error}</span></div>}
        </div>

        <div className="verify-claims">
          <div className="col-head"><div><span className="idx">02</span><h2>What this checks</h2></div></div>
          <ul className="claim-list">
            <li><Check size={14} /> The record's contents have not been modified since it was sealed</li>
            <li><Check size={14} /> Its SHA-256 fingerprint still matches the value committed on-chain</li>
            <li><Check size={14} /> The on-chain record exists and is readable from the configured chain</li>
          </ul>
          <div className="claim-caveat">
            <TriangleAlert size={15} />
            <div>
              <strong>What it does not claim</strong>
              <span>
                The blockchain cannot tell you whether a discovered post is truthful, or that the person in it
                is who the record says. It only proves this record has not changed since it was registered.
              </span>
            </div>
          </div>
        </div>

        <div className="verify-outcome">
          <div className="col-head"><div><span className="idx">03</span><h2>Result</h2></div></div>
          {!result ? (
            <div className="output-empty">
              <ShieldCheck className="icon" size={28} />
              <strong>No record submitted yet</strong>
              <p>Upload an evidence file to compare its fingerprint against the chain.</p>
            </div>
          ) : (
            <div className={`verdict-block ${verified ? "ok" : "bad"}`}>
              <span className={`badge ${verified ? "success" : "danger"}`}>{verdict}</span>
              <p className="verdict-reason">{show(result.reason ?? (verified ? "The recalculated hash matches the on-chain commitment." : "The recalculated hash does not match the on-chain commitment."))}</p>
              <div className="hash-block">
                <small>Recalculated locally</small>
                <code>{show(result.local_hash)}</code>
              </div>
              <div className="hash-block">
                <small>Stored on-chain</small>
                <code>{show(result.blockchain_hash)}</code>
              </div>
              <details className="raw-json">
                <summary><Hash size={13} /> Full response</summary>
                <pre className="json-viewer">{JSON.stringify(result, null, 2)}</pre>
              </details>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
