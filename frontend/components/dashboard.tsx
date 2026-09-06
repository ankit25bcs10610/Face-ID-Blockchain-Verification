"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  Activity,
  ArrowUpRight,
  Check,
  CheckCircle2,
  CircleAlert,
  Copy,
  Database,
  FileCheck2,
  Fingerprint,
  GitBranch,
  Image as ImageIcon,
  Link2,
  LoaderCircle,
  LockKeyhole,
  ScanFace,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  X,
  XCircle
} from "lucide-react";
import { ChangeEvent, DragEvent, useEffect, useMemo, useRef, useState } from "react";
import { getHealth, runPipeline } from "@/lib/api";
import type { Candidate, ConnectionState, PipelineResponse, PipelineStage, StageState } from "@/lib/types";

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
  return typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "No data";
}

function display(value?: unknown) {
  return value === undefined || value === null || value === "" ? "No data available" : String(value);
}

function metadata(candidate?: Candidate) {
  return candidate?.metadata ?? {};
}

function StageIcon({ state }: { state: StageState }) {
  if (state === "processing") return <LoaderCircle className="spin" size={16} />;
  if (state === "success") return <Check size={16} />;
  if (state === "failed") return <X size={16} />;
  return <span className="stage-dot" />;
}

function CopyButton({ value }: { value?: string }) {
  const [copied, setCopied] = useState(false);
  if (!value) return null;
  return (
    <button className="icon-button" aria-label="Copy value" onClick={() => void navigator.clipboard.writeText(value).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1400); })}>
      {copied ? <Check size={15} /> : <Copy size={15} />}
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
  const [apiState, setApiState] = useState<ConnectionState>("checking");
  const [chainState, setChainState] = useState<ConnectionState>("checking");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getHealth().then((health) => {
      setApiState(health.status === "healthy" || health.status === "degraded" ? "connected" : "disconnected");
      setChainState(health.blockchain?.connected || health.blockchain?.status === "connected" || health.components?.blockchain === "available" ? "connected" : "disconnected");
    }).catch(() => { setApiState("disconnected"); setChainState("disconnected"); });
  }, []);

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  const candidateResults = result?.search?.results ?? (result?.candidate ? [result.candidate] : []);
  const best = result?.candidate ?? candidateResults[0];
  const bestMetadata = metadata(best);
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
    try {
      const response = await runPipeline(file);
      setResult(response);
      setStages(initialStages.map((stage) => ({ ...stage, state: "success" })));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The pipeline request failed.");
      setStages((current) => current.map((stage, index) => ({ ...stage, state: index === 0 ? "failed" : "pending" })));
    } finally { setRunning(false); }
  };

  const connectionLabel = (state: ConnectionState) => state === "checking" ? "Checking" : state === "connected" ? "Connected" : "Unavailable";
  const connectionClass = (state: ConnectionState) => state === "connected" ? "online" : state === "checking" ? "checking" : "offline";
  const topCandidates = useMemo(() => candidateResults.slice(1), [candidateResults]);

  return (
    <main className="app-shell">
      <div className="ambient ambient-one" /><div className="ambient ambient-two" />
      <nav className="topbar">
        <div className="brand"><div className="brand-mark"><GitBranch size={19} /></div><div><strong>TRACECHAIN <span>AI</span></strong><small>Identify · Discover · Verify</small></div></div>
        <div className="top-status">
          <div className="status-pill"><i className={connectionClass(apiState)} /> API {connectionLabel(apiState)}</div>
          <div className="status-pill"><i className={connectionClass(chainState)} /> Chain {connectionLabel(chainState)}</div>
        </div>
      </nav>

      <section className="hero">
        <div><p className="eyebrow"><Sparkles size={14} /> AUTHORIZED EVIDENCE INTELLIGENCE</p><h1>Faces to facts.<br /><em>On chain.</em></h1><p className="hero-copy">Process authorized visual evidence, discover matching content, and create tamper-evident verification records.</p></div>
        <div className="hero-orbit"><div className="orbit-core"><ShieldCheck size={30} /><span>TRUST<br />LAYER</span></div><div className="orbit orbit-a" /><div className="orbit orbit-b" /><span className="orbit-label label-a">AI</span><span className="orbit-label label-b">WEB3</span></div>
      </section>

      <div className="workspace-grid">
        <section className="panel upload-panel">
          <div className="panel-heading"><div><p className="section-kicker">01 / INPUT</p><h2>Face scan</h2></div><ScanFace size={22} /></div>
          <div className={`dropzone ${dragging ? "dragging" : ""} ${preview ? "has-preview" : ""}`} onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={handleDrop} onClick={() => inputRef.current?.click()} role="button" tabIndex={0} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") inputRef.current?.click(); }}>
            {preview ? <><img src={preview} alt="Selected face scan preview" /><div className="preview-overlay"><span><FileCheck2 size={15} /> {file?.name}</span><b>{file ? `${(file.size / 1024 / 1024).toFixed(2)} MB` : ""}</b></div></> : <><div className="upload-icon"><UploadCloud size={25} /></div><strong>Drop your authorized scan here</strong><span>or click to browse your files</span><small>JPG · JPEG · PNG <b>·</b> max 10 MB</small></>}
            <input ref={inputRef} type="file" accept="image/jpeg,image/png" onChange={handleInput} hidden />
          </div>
          {file && <button className="remove-button" onClick={(event) => { event.stopPropagation(); removeFile(); }}><X size={14} /> Remove scan</button>}
          <div className="consent-note"><LockKeyhole size={14} /><span>Authorized content only. Your scan is processed by the configured backend.</span></div>
          <button className="primary-button" disabled={!file || running} onClick={run}>{running ? <><LoaderCircle className="spin" size={17} /> Processing pipeline...</> : <><Activity size={17} /> Run TraceChain pipeline <ArrowUpRight size={16} /></>}</button>
          {error && <div className="error-box"><CircleAlert size={17} /><span>{error}</span></div>}
        </section>

        <section className="panel pipeline-panel"><div className="panel-heading"><div><p className="section-kicker">02 / PIPELINE</p><h2>Live trace</h2></div><span className="run-id">{result?.pipeline_id ? `RUN ${result.pipeline_id.slice(0, 8).toUpperCase()}` : "AWAITING INPUT"}</span></div><div className="pipeline-list">{stages.map((stage, index) => <div className={`pipeline-stage ${stage.state}`} key={stage.id}><div className="stage-index">{String(index + 1).padStart(2, "0")}</div><div className="stage-line"><span className="stage-icon"><StageIcon state={stage.state} /></span><span>{stage.label}</span></div><span className="stage-state">{stage.state}</span></div>)}</div></section>
      </div>

      <AnimatePresence>{result && <motion.section className="results-section" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}><div className="results-header"><div><p className="eyebrow"><CheckCircle2 size={14} /> RUNTIME RESULTS</p><h2>Evidence report</h2></div><span className={`verdict-badge ${verdictTone}`}>{verdict ?? "No verdict"}</span></div>
        <div className="results-grid">
          <div className="result-card face-result"><div className="card-title"><ScanFace size={17} /><span>Face analysis</span></div>{preview ? <img className="result-thumb" src={preview} alt="Input face" /> : <div className="empty-thumb"><ImageIcon size={23} /></div>}<div className="metric-row"><span>Face detected</span><b>{result.match ? "Returned by API" : "No data available"}</b></div><div className="metric-row"><span>Embedding</span><b>{result.search ? "Generated by API" : "No data available"}</b></div></div>
          <div className="result-card"><div className="card-title"><Database size={17} /><span>Top match</span></div>{best ? <><div className="candidate-title"><strong>{display(best.post_id)}</strong><span>{formatPercent(best.similarity_score)}</span></div><p className="caption">{display(bestMetadata.caption)}</p><div className="metric-row"><span>Provider</span><b>{display(result.search?.provider)}</b></div><div className="metric-row"><span>Source</span><b>{display(bestMetadata.platform)}</b></div><div className="metric-row"><span>Published</span><b>{display(bestMetadata.timestamp)}</b></div></> : <div className="empty-state">No candidate data returned.</div>}</div>
          <div className={`result-card verdict-card ${verdictTone}`}><div className="card-title"><ShieldCheck size={17} /><span>Match analysis</span></div><div className="confidence-value">{formatPercent(result.match?.confidence)}</div><span className="confidence-label">final confidence</span><div className="signal"><span>Face similarity</span><div><i style={{ width: `${Math.min(100, (result.match?.face_similarity ?? 0) * 100)}%` }} /><b>{formatPercent(result.match?.face_similarity)}</b></div></div><div className="signal"><span>Image similarity</span><div><i style={{ width: `${Math.min(100, (result.match?.image_similarity ?? 0) * 100)}%` }} /><b>{formatPercent(result.match?.image_similarity)}</b></div></div><div className="signal"><span>Metadata consistency</span><div><i style={{ width: `${Math.min(100, (result.match?.metadata_consistency ?? 0) * 100)}%` }} /><b>{formatPercent(result.match?.metadata_consistency)}</b></div></div></div>
        </div>
        <div className="results-grid lower-grid"><div className="result-card evidence-card"><div className="card-title"><Fingerprint size={17} /><span>Cryptographic evidence</span></div><div className="data-line"><span>Evidence ID</span><div>{display(result.evidence?.evidence_id)} <CopyButton value={typeof result.evidence?.evidence_id === "string" ? result.evidence.evidence_id : undefined} /></div></div><div className="data-line"><span>Pipeline ID</span><div>{display(result.pipeline_id)} <CopyButton value={result.pipeline_id} /></div></div><div className="hash-box"><small>SHA-256 fingerprint</small><code>{display(result.evidence_hash)}</code><CopyButton value={result.evidence_hash} /></div></div><div className="result-card chain-card"><div className="card-title"><Link2 size={17} /><span>Blockchain record</span></div><div className="data-line"><span>Contract</span><div>{display(result.blockchain?.contract_address)} <CopyButton value={result.blockchain?.contract_address} /></div></div><div className="data-line"><span>Transaction</span><div>{display(result.blockchain?.transaction_hash)} <CopyButton value={result.blockchain?.transaction_hash} /></div></div><div className="data-line"><span>Block</span><div>{display(result.blockchain?.block_number)}</div></div><div className="data-line"><span>Timestamp</span><div>{display(result.blockchain?.timestamp)}</div></div></div></div>
        {topCandidates.length > 0 && <div className="candidate-strip"><div className="card-title"><Database size={17} /><span>Other candidates · {topCandidates.length}</span></div>{topCandidates.map((item) => <div className="candidate-row" key={item.post_id}><span>{display(item.post_id)}</span><b>{formatPercent(item.similarity_score)}</b><small>{display(item.metadata?.platform)}</small></div>)}</div>}
      </motion.section>}</AnimatePresence>

      <footer><span><span className="footer-mark">TC</span> TRACECHAIN AI</span><span>Authorized evidence infrastructure <b>·</b> no fabricated runtime data</span><span>v1.0 / LOCAL CORE</span></footer>
    </main>
  );
}
