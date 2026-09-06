"use client";

import {
  Activity,
  ArrowRight,
  Check,
  CircleAlert,
  Copy,
  FileCheck2,
  Fingerprint,
  Hash,
  Image as ImageIcon,
  Link2,
  LoaderCircle,
  LockKeyhole,
  ScanFace,
  ShieldCheck,
  UploadCloud,
  X
} from "lucide-react";
import { ChangeEvent, DragEvent, useEffect, useRef, useState } from "react";
import SiteNav from "@/components/site-nav";
import { runPipeline } from "@/lib/api";
import { platformFor } from "@/lib/platform";
import type { Candidate, PipelineResponse, PipelineStage, StageState } from "@/lib/types";

const stageLabels = [
  ["validation", "Image validation"],
  ["detection", "Face detection"],
  ["embedding", "Face embedding"],
  ["discovery", "Content discovery"],
  ["vector", "Vector similarity search"],
  ["matching", "Match verification"],
  ["evidence", "Evidence generation"],
  ["hash", "SHA-256 hashing"],
  ["chain", "Blockchain registration"],
  ["reverify", "Re-verification"]
] as const;

const initialStages: PipelineStage[] = stageLabels.map(([id, label]) => ({ id, label, state: "pending" }));

function formatPercent(value?: number | null) {
  return typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "—";
}

function display(value?: unknown) {
  return value === undefined || value === null || value === "" ? "—" : String(value);
}

function metadataOf(candidate?: Candidate) {
  return candidate?.metadata ?? {};
}

function StageDot({ state }: { state: StageState }) {
  if (state === "processing") return <LoaderCircle className="spin" size={13} />;
  if (state === "success") return <Check size={13} />;
  if (state === "failed") return <X size={13} />;
  return <span className="dot" />;
}

function CopyIcon({ value }: { value?: string }) {
  const [copied, setCopied] = useState(false);
  if (!value) return null;
  return (
    <button
      className="icon-btn"
      aria-label="Copy value"
      onClick={() =>
        void navigator.clipboard.writeText(value).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1300);
        })
      }
    >
      {copied ? <Check size={13} /> : <Copy size={13} />}
    </button>
  );
}

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [running, setRunning] = useState(false);
  const [stages, setStages] = useState(initialStages);
  const [result, setResult] = useState<PipelineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [runsThisSession, setRunsThisSession] = useState(0);
  const [matchesThisSession, setMatchesThisSession] = useState(0);
  const [evidenceThisSession, setEvidenceThisSession] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  const candidateResults = result?.search?.results ?? (result?.candidate ? [result.candidate] : []);
  const best = result?.candidate ?? candidateResults[0];
  const bestMetadata = metadataOf(best);
  const verdict = result?.reverification?.status ?? (result?.match?.match ? "MATCH VERIFIED" : result ? "NO MATCH" : null);
  const verdictTone = verdict === "VERIFIED" || verdict === "MATCH VERIFIED" ? "success" : verdict ? "danger" : "neutral";

  const chooseFile = (next: File | undefined) => {
    if (!next) return;
    if (!next.type.match(/^image\/(jpeg|png)$/)) { setError("Please choose a JPG, JPEG, or PNG image."); return; }
    if (next.size > 10 * 1024 * 1024) { setError("The selected image is larger than 10 MB."); return; }
    setError(null); setResult(null); setStages(initialStages); setFile(next);
    setPreview(URL.createObjectURL(next));
  };

  const handleInput = (event: ChangeEvent<HTMLInputElement>) => chooseFile(event.target.files?.[0]);
  const handleDrop = (event: DragEvent<HTMLDivElement>) => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files?.[0]); };
  const removeFile = () => { if (preview) URL.revokeObjectURL(preview); setFile(null); setPreview(null); setResult(null); setStages(initialStages); };

  const run = async () => {
    if (!file || running) return;
    setRunning(true); setError(null); setResult(null);
    setStages(initialStages.map((stage, index) => ({ ...stage, state: index === 0 ? "processing" : "pending" })));
    setRunsThisSession((count) => count + 1);
    try {
      const response = await runPipeline(file);
      setResult(response);
      setStages(initialStages.map((stage) => ({ ...stage, state: "success" })));
      if (response.match?.match) setMatchesThisSession((count) => count + 1);
      if (response.evidence_hash) setEvidenceThisSession((count) => count + 1);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The pipeline request failed.");
      setStages((current) => current.map((stage, index) => ({ ...stage, state: index === 0 ? "failed" : "pending" })));
    } finally { setRunning(false); }
  };

  return (
    <main>
      <SiteNav />

      <section className="hero">
        <div>
          <p className="kicker">Authorized evidence intelligence</p>
          <h1>From a face scan to a <i>verifiable record</i>.</h1>
          <p className="lede">
            Upload an authorized image. TraceChain searches the open web for a genuine matching post,
            re-verifies the match with its own face model, and seals the result on-chain.
          </p>
        </div>
        <div className="hero-meta">
          <div><strong>Live web search</strong>Google Lens, not a fixed dataset</div>
          <div><strong>Local Ethereum chain</strong>Ganache · chain 1337</div>
        </div>
      </section>

      <section className="stat-strip">
        <div className="stat"><div className="num">{runsThisSession}</div><div className="label">Scans run this session</div></div>
        <div className="stat"><div className="num">{matchesThisSession}</div><div className="label">Matches confirmed</div></div>
        <div className="stat"><div className="num">{evidenceThisSession}</div><div className="label">Evidence records sealed</div></div>
        <div className="stat"><div className="num">{verdict ?? "Ready"}</div><div className="label">Latest verdict</div></div>
      </section>

      <section className="workspace">
        <div className="col">
          <div className="col-head">
            <div><span className="idx">01</span><h2>Face scan</h2></div>
            <ScanFace size={20} color="var(--gold)" />
          </div>
          <div
            className={`dropzone ${dragging ? "dragging" : ""} ${preview ? "has-preview" : ""}`}
            onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            role="button" tabIndex={0}
            onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") inputRef.current?.click(); }}
          >
            {preview ? (
              <>
                <img src={preview} alt="Selected face scan preview" />
                <div className="preview-tag"><span><FileCheck2 size={13} /> {file?.name}</span><b>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : ""}</b></div>
              </>
            ) : (
              <>
                <UploadCloud className="icon" size={26} />
                <strong>Drop your authorized scan here</strong>
                <span>or click to browse your files</span>
                <small>JPG · PNG &nbsp;·&nbsp; max 10 MB</small>
              </>
            )}
            <input ref={inputRef} type="file" accept="image/jpeg,image/png" onChange={handleInput} hidden />
          </div>
          {file && <button className="remove-scan" onClick={(event) => { event.stopPropagation(); removeFile(); }}><X size={13} /> Remove scan</button>}
          <div className="consent-line"><LockKeyhole size={14} /><span>Authorized content only. To search the web, this image is briefly hosted at a public URL so it can be fetched — it is not kept private during that step.</span></div>
          <button className="run-btn" disabled={!file || running} onClick={run}>
            {running ? <><LoaderCircle className="spin" size={16} /> Processing pipeline…</> : <><Activity size={16} /> Run TraceChain pipeline</>}
          </button>
          {error && <div className="error-line"><CircleAlert size={15} /><span>{error}</span></div>}
        </div>

        <div className="col">
          <div className="col-head">
            <div><span className="idx">02</span><h2>Live trace</h2></div>
            <span className="col-head tag" style={{ padding: 0 }}>
              <span className="tag">{result?.pipeline_id ? `Run ${result.pipeline_id.slice(0, 8)}` : "Awaiting input"}</span>
            </span>
          </div>
          <div className="trace-list">
            {stages.map((stage, index) => (
              <div className={`trace-row ${stage.state}`} key={stage.id}>
                <span className="n">{String(index + 1).padStart(2, "0")}</span>
                <span style={{ display: "flex", alignItems: "center", gap: 9 }}>
                  <StageDot state={stage.state} /> {stage.label}
                </span>
                <span className="state">{stage.state}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="col">
          <div className="col-head">
            <div><span className="idx">03</span><h2>Evidence &amp; verification</h2></div>
          </div>
          {!result ? (
            <div className="output-empty">
              <ShieldCheck className="icon" size={30} />
              <strong>Run a scan to generate evidence</strong>
              <p>A verified match, its source, a content hash, and an on-chain record will appear here.</p>
              <div className="output-icons">
                <div><Link2 size={16} /><span>Source</span></div>
                <div><Hash size={16} /><span>Hash</span></div>
                <div><ShieldCheck size={16} /><span>Chain proof</span></div>
                <div><FileCheck2 size={16} /><span>Verdict</span></div>
              </div>
            </div>
          ) : (
            <div className="verdict-block">
              <span className={`badge ${verdictTone}`}>{verdict ?? "No verdict"}</span>
              <div className="confidence">{formatPercent(result.match?.confidence)}</div>
              <div className="confidence-label">final match confidence</div>
              <div className="match-line"><span>Top source</span><b>{display(bestMetadata.platform)}</b></div>
              <div className="match-line"><span>Evidence hash</span><b style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>{result.evidence_hash ? `${result.evidence_hash.slice(0, 10)}…` : "—"}</b></div>
              <a className="jump-link" href="#results">View full evidence report <ArrowRight size={13} /></a>
            </div>
          )}
        </div>
      </section>

      {result && (
        <section className="results" id="results">
          <div className="results-head">
            <div><p className="kicker">Runtime results — nothing below is fabricated</p><h2>Evidence report</h2></div>
          </div>

          {candidateResults.length > 0 && (
            <div className="match-list">
              {candidateResults.map((item, index) => {
                const href = typeof item.post_id === "string" && item.post_id.startsWith("http") ? item.post_id : undefined;
                const { Icon, label } = platformFor(href ?? String(item.metadata?.platform ?? ""));
                const title = String(item.metadata?.title ?? item.metadata?.caption ?? item.post_id ?? "Untitled source");
                return (
                  <a
                    className={`match-row${href ? "" : " no-link"}`}
                    key={`${item.post_id}-${index}`}
                    href={href}
                    target={href ? "_blank" : undefined}
                    rel={href ? "noreferrer" : undefined}
                  >
                    <span className="platform-icon"><Icon size={16} /></span>
                    <span className="info"><span className="platform">{label}</span><span className="title">{title}</span></span>
                    {index === 0 && <span className="best-tag">Best match</span>}
                    <span className="score">{formatPercent(item.similarity_score)}<small>similarity</small></span>
                  </a>
                );
              })}
            </div>
          )}

          <div className="grid-2">
            <div className="card">
              <div className="card-title"><ImageIcon size={14} /> FACE ANALYSIS</div>
              {preview && <img src={preview} alt="Input face" style={{ width: 84, height: 84, objectFit: "cover", borderRadius: 4, border: "1px solid var(--line)", marginBottom: 14 }} />}
              <div className="data-row"><span>Face detected</span><span className="val">{result.match ? "Yes" : "—"}</span></div>
              <div className="data-row"><span>Embedding</span><span className="val">{result.search ? "512-d ArcFace" : "—"}</span></div>
              <div className="data-row"><span>Search provider</span><span className="val">{display(result.search?.provider)}</span></div>
              <div className="signal-bar">
                <span>Face similarity</span>
                <div className="track"><i style={{ width: `${Math.min(100, (result.match?.face_similarity ?? 0) * 100)}%` }} /></div>
                <span className="value">{formatPercent(result.match?.face_similarity)}</span>
              </div>
              <div className="signal-bar">
                <span>Image similarity</span>
                <div className="track"><i style={{ width: `${Math.min(100, (result.match?.image_similarity ?? 0) * 100)}%` }} /></div>
                <span className="value">{formatPercent(result.match?.image_similarity)}</span>
              </div>
              <div className="signal-bar">
                <span>Metadata consistency</span>
                <div className="track"><i style={{ width: `${Math.min(100, (result.match?.metadata_consistency ?? 0) * 100)}%` }} /></div>
                <span className="value">{formatPercent(result.match?.metadata_consistency)}</span>
              </div>
            </div>

            <div className="card">
              <div className="card-title"><Fingerprint size={14} /> CRYPTOGRAPHIC EVIDENCE</div>
              <div className="data-row"><span>Evidence ID</span><span className="val">{display(result.evidence?.evidence_id)} <CopyIcon value={typeof result.evidence?.evidence_id === "string" ? result.evidence.evidence_id : undefined} /></span></div>
              <div className="data-row"><span>Pipeline ID</span><span className="val">{display(result.pipeline_id)} <CopyIcon value={result.pipeline_id} /></span></div>
              <div className="hash-block">
                <small>SHA-256 fingerprint</small>
                <code>{display(result.evidence_hash)}</code>
                <div style={{ position: "absolute", right: 10, top: 30 }}><CopyIcon value={result.evidence_hash} /></div>
              </div>
            </div>
          </div>

          <div className="grid-2">
            <div className="card">
              <div className="card-title"><Link2 size={14} /> BLOCKCHAIN RECORD</div>
              <div className="data-row"><span>Contract</span><span className="val">{display(result.blockchain?.contract_address)} <CopyIcon value={result.blockchain?.contract_address} /></span></div>
              <div className="data-row"><span>Transaction</span><span className="val">{display(result.blockchain?.transaction_hash)} <CopyIcon value={result.blockchain?.transaction_hash} /></span></div>
              <div className="data-row"><span>Block</span><span className="val">{display(result.blockchain?.block_number)}</span></div>
              <div className="data-row"><span>Timestamp</span><span className="val">{display(result.blockchain?.timestamp)}</span></div>
            </div>
            <div className="card">
              <div className="card-title"><ShieldCheck size={14} /> RE-VERIFICATION</div>
              <div className="data-row"><span>Status</span><span className="val">{display(result.reverification?.status)}</span></div>
              <div className="data-row"><span>Local hash</span><span className="val">{result.reverification?.local_hash ? `${result.reverification.local_hash.slice(0, 14)}…` : "—"}</span></div>
              <div className="data-row"><span>On-chain hash</span><span className="val">{result.reverification?.blockchain_hash ? `${result.reverification.blockchain_hash.slice(0, 14)}…` : "—"}</span></div>
              <div className="data-row"><span>Reason</span><span className="val">{display(result.reverification?.reason)}</span></div>
            </div>
          </div>
        </section>
      )}

      <footer className="site-footer">
        <span><strong>TraceChain AI</strong> — authorized evidence infrastructure</span>
        <span>No fabricated runtime data</span>
        <span>v1.0 · local core</span>
      </footer>
    </main>
  );
}
