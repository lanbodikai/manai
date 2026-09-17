import {useEffect,useRef} from "react";
import {CheckCircle2,TriangleAlert,X} from "lucide-react";
import type {DecisionRow,OptimizeReceipt} from "../api/optimization";
import {number} from "../format";
import {taskSummary} from "../optimization-options";

export function OptimizeDialog({rows,share,hours,jobs,overlap,sending,error,receipt,ready,onProceed,onReturn}:{
  rows:DecisionRow[];share:number;hours:number;jobs:number;overlap:number;sending:boolean;error:string;
  receipt:OptimizeReceipt|null;ready:boolean;onProceed:()=>void;onReturn:()=>void;
}) {
  const dialog=useRef<HTMLDialogElement>(null);
  const returnButton=useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const prior=document.activeElement as HTMLElement|null;
    const element=dialog.current;
    element?.showModal();returnButton.current?.focus();
    return () => {element?.close();if(prior?.isConnected) prior.focus();};
  },[]);
  return <dialog ref={dialog} className="optimize-dialog" aria-labelledby="optimize-dialog-title" aria-describedby="optimize-dialog-description" onKeyDown={e => {
    if(e.key!=="Tab") return;
    const items=Array.from(e.currentTarget.querySelectorAll<HTMLElement>("button:not(:disabled), a[href], summary, [tabindex='0']")).filter(el => el.getClientRects().length>0);
    const first=items[0],last=items[items.length-1];
    if(e.shiftKey && document.activeElement===first) {e.preventDefault();last?.focus();}
    if(!e.shiftKey && document.activeElement===last) {e.preventDefault();first?.focus();}
  }} onCancel={e => {e.preventDefault();onReturn();}}>
    <header><div><span className="eyebrow">REVIEW BEFORE PROCEEDING</span><h2 id="optimize-dialog-title">Optimize {rows.length} selected {rows.length===1 ? "task" : "tasks"}?</h2></div><button className="icon-button" aria-label="Return to decisions" onClick={onReturn}><X size={20}/></button></header>
    <div className="optimize-dialog-body">
      <p id="optimize-dialog-description">Proceed requests a model. No workloads change.</p>
      <p className="optimize-scope"><strong>{share>0 && share<.1 ? "<0.1" : share.toFixed(1)}%</strong> of recorded GPU time affected · not savings</p>
      <div className="optimize-risk-list">{rows.map(row => <article key={row.id} aria-label={row.title}><h3>{row.title}</h3><p>{taskSummary[row.id]?.fix ?? row.fix}</p><div className="optimize-risk"><TriangleAlert size={17}/><div><h4>What could go wrong?</h4><p>{taskSummary[row.id]?.risk ?? row.risk}</p></div></div><details><summary>Safeguards and owner</summary><p>{row.risk}</p><p>Owner: {row.owner}</p></details></article>)}</div>
      <details className="optimize-method"><summary>Calculation details</summary><p>{number(hours)} GPU-hours across {number(jobs)} unique jobs. {number(overlap)} overlapping GPU-hours counted only once. Financial savings have not been verified.</p></details>
      {!ready && !sending && !receipt && <p role="alert">The selection or source changed. Return to the table and review it again.</p>}
      {error && <div className="optimization-error" role="alert"><TriangleAlert size={18}/><div><strong>Optimization was not confirmed</strong><p>{error}</p><p>Your selected tasks are preserved.</p></div></div>}
      {receipt && <div className="optimization-receipt" role="status"><CheckCircle2 size={19}/><div><strong>{receipt.synthetic ? "Synthetic example — request accepted" : "Backend accepted your modeling request"}</strong><p>Request {receipt.optimization_id}. No workload change or savings has been verified.</p></div></div>}
      {sending && <p role="status">Submitting your request… Returning does not cancel a request already sent.</p>}
    </div>
    <footer><button ref={returnButton} className="secondary" onClick={onReturn}>Return</button><button className="primary" disabled={!ready || sending || !!receipt} onClick={onProceed}>{sending ? "Submitting…" : receipt ? "Request accepted" : error ? "Retry proceed" : "Proceed"}</button></footer>
  </dialog>;
}
