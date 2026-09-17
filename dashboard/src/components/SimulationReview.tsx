import {useEffect,useRef,useState} from 'react';
import {ArrowUp,BookOpen,LoaderCircle,Sparkles} from 'lucide-react';
import type {ModelState} from './PortfolioModel';
import {titles,type Action,type EvidencePage} from '../api/portfolio';

type Review={contract_version:'portfolio-review-1';simulation_id:string;dataset_version:string;client_request_id:string;action:string;
 status:'ok'|'insufficient_evidence';answer:string;checks:{id:string;status:'pass'|'fail'|'unknown';message:string}[];
 coverage:{retrieved:number;total:number;complete:boolean};limitations:string[];source_examples:EvidencePage['items'];
 usage:{model:string|null;provider:string|null;tool_calls:number;analysis_reads:number;latency_ms:number};tool_trace_ids:string[]};

export function SimulationReview({model}:{model:ModelState}){
 const r=model.result;
 const [question,setQuestion]=useState(''),[action,setAction]=useState('all'),[answer,setAnswer]=useState<Review|null>(null);
 const [asked,setAsked]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const seq=useRef(0),controller=useRef<AbortController|null>(null);
 useEffect(()=>{++seq.current;controller.current?.abort();setAnswer(null);setError('');setAsked('');setBusy(false);setAction('all');return()=>{++seq.current;controller.current?.abort();};},[r?.simulation_id]);
 async function ask(text:string){
  if(!r||busy||!text.trim())return;
  const current=++seq.current,id=crypto.randomUUID(),abort=new AbortController();controller.current=abort;
  const timer=setTimeout(()=>abort.abort(),35000);
  setBusy(true);setError('');setAnswer(null);setAsked(text);setQuestion(text);
  try{
   const response=await fetch(`/api/portfolio-simulations/${r.simulation_id}/review`,{method:'POST',signal:abort.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({client_request_id:id,question:text,dataset_version:r.dataset_version,action})});
   if(!response.ok){let message='Optional simulation reviewer is unavailable. Your calculation and export remain available.';try{const body=await response.json();if(typeof body.error?.message==='string')message=body.error.message;}catch{}throw new Error(message);}
   const result=await response.json() as Review;
   if(result.contract_version!=='portfolio-review-1'||result.simulation_id!==r.simulation_id||result.dataset_version!==r.dataset_version||result.client_request_id!==id||result.action!==action||!['ok','insufficient_evidence'].includes(result.status)||typeof result.answer!=='string'||!Array.isArray(result.checks)||!Array.isArray(result.source_examples)||!Array.isArray(result.limitations)||!Array.isArray(result.tool_trace_ids)||!result.coverage||!result.usage)throw new Error('Review does not match this simulation. Recalculate or retry.');
   if(current===seq.current)setAnswer(result);
  }catch(e){if(current===seq.current)setError(e instanceof Error&&e.name==='AbortError'?'Review timed out. Your calculation remains available.':e instanceof Error?e.message:'Review unavailable.');}
  finally{clearTimeout(timer);if(current===seq.current)setBusy(false);}
 }
 return <section className="panel simulation-review" aria-label="Simulation evidence review">
  <div className="section-heading"><div><span className="eyebrow">FOLLOW THE NUMBER BACK</span><h2>Review this cost estimate</h2></div><Sparkles size={22}/></div>
  <p>Ask where a number comes from, which assumptions support it, or what could make it wrong. The optional Featherless model selects relevant evidence; calculations and quotations come from the saved simulation.</p>
  {!r?<p role="status">{model.busy?'Preparing the simulation…':'Calculate a simulation in Model before requesting its review.'}</p>:<>
   {model.dirty&&<p role="status" className="pilot-warning">Assumptions changed. Review uses the previous calculated result; recalculate in Model to review your edits.</p>}
   <label>Review scope <select aria-label="Review scope" value={action} disabled={busy} onChange={e=>{setAction(e.target.value);setAnswer(null);setAsked('');setError('');}}><option value="all">Combined portfolio</option>{r.actions.map(a=><option key={a.id} value={a.id}>{titles[a.id]}</option>)}</select></label>
   <div className="conversation-suggestions">{['Trace this cost estimate back to its evidence.','Which assumptions are untested?','What would make this estimate wrong?'].map(q=><button key={q} disabled={busy} onClick={()=>void ask(q)}>{q}</button>)}</div>
   <form className="conversation-composer" onSubmit={e=>{e.preventDefault();void ask(question);}}><label className="sr-only" htmlFor="simulation-question">Simulation review question</label><textarea id="simulation-question" rows={2} maxLength={2000} value={question} placeholder="Ask about this estimate…" onChange={e=>setQuestion(e.target.value)}/><button className="conversation-send" aria-label="Ask simulation reviewer" disabled={busy||!question.trim()}>{busy?<LoaderCircle/>:<ArrowUp/>}</button></form>
   {busy&&<p role="status">Retrieving the frozen calculation and evidence, then reviewing the assumptions…</p>}
   {error&&<div role="alert" className="error"><p>{error}</p><button className="text-button" onClick={()=>void ask(asked)}>Retry simulation review</button></div>}
   {answer&&<div className="simulation-review-answer" role="status"><p className="user-message">{asked}</p><p className="badge">{answer.usage.model?'Featherless-assisted review':'Deterministic review · no model'}</p><p><strong>{answer.checks.filter(c=>c.status==='fail').length} failed checks · {answer.checks.filter(c=>c.status==='unknown').length} unknown checks</strong></p><p>Evidence coverage: {answer.coverage.retrieved} / {answer.coverage.total} records in this scope. {answer.coverage.complete?'All scoped records retrieved.':'Partial retrieval; full cohort totals are not certified.'}</p>
    <p className="assistant-text">{answer.answer}</p>
    <details><summary>Inspect retrieved source examples <BookOpen size={14}/></summary>{answer.source_examples.map(row=><details key={row.job_id}><summary>Job {row.job_id} · {row.assigned_action?titles[row.assigned_action as Action]:'Excluded'}</summary><p>Source inputs and per-job calculations from this exact frozen simulation:</p><pre>{JSON.stringify(row,null,2)}</pre></details>)}</details>
    <details><summary>All checks and model details</summary>{answer.checks.map(c=><p key={c.id}><b>{c.status.toUpperCase()}</b>: {c.message}</p>)}<p>Model: {answer.usage.model??'none'} · {answer.usage.tool_calls} MCP operations · {answer.usage.analysis_reads} analysis reads.</p><p>Simulation: {answer.simulation_id}</p></details>
   </div>}
   <p className="small muted"><a href="#model">Inspect or recalculate this simulation →</a> · Model failure does not change the results or claims.</p>
  </>}
 </section>;
}
