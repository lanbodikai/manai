import { useEffect, useRef, useState } from "react";
import { MessageSquare, Sparkles, ArrowUpRight, ArrowUp, SquarePen, BookOpen, LoaderCircle } from "lucide-react";
import "../chat.css";
import type { Audit, DashboardApi, Explanation } from "../api/types";
import type {ModelState} from './PortfolioModel';
import {SimulationReview} from './SimulationReview';
import {
  ApiError,
  assertAuditId,
  assertRequestId,
  errorMessage,
} from "../api/validation";

function QuestionPanel({
  advanced,
  api,
  audit,
  mock,
  onEvidence,
}: {
  advanced: boolean;
  api: DashboardApi;
  audit: Audit;
  mock: boolean;
  onEvidence: (id: string) => void;
}) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Explanation | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const sequence = useRef(0);
  useEffect(
    () => () => {
      sequence.current++;
    },
    [],
  );
  async function ask(text: string) {
    const seq = ++sequence.current;
    setBusy(true);
    setError("");
    setAnswer(null);
    setQuestion(text);
    const request = { client_request_id: crypto.randomUUID(), question: text };
    try {
      const result = assertRequestId(
        assertAuditId(
          await (advanced
            ? api.explainAudit(audit.audit_id, request)
            : api.askBaseChat(audit.audit_id, request)),
          audit.audit_id,
        ),
        request.client_request_id,
      );
      if (seq === sequence.current) setAnswer(result);
    } catch (e) {
      if (seq === sequence.current) setError(errorMessage(e));
    } finally {
      if (seq === sequence.current) setBusy(false);
    }
  }
  return (
    <div className={advanced ? "question-panel advanced" : "question-panel"}>
      <h3>
        {advanced ? <Sparkles size={18} /> : <MessageSquare size={18} />}
        {advanced ? "Advanced reviewer" : "Pilot assistant"}
        <span className="badge">
          {advanced ? "Optional" : "MCP · evidence-backed"}
        </span>
      </h3>
      <p className="small muted">
        {mock
          ? "Example responses only. No live data, model or MCP calls."
          : advanced
            ? "An optional deeper review. The rest of the dashboard works independently."
            : "Ask why CPU placement is worth testing, which jobs qualify, or what could go wrong."}
      </p>
      {!advanced && (
        <div className="question-chips">
          {[
            "Why this pilot?",
            "Which jobs are eligible?",
            "What are the recovery assumptions?",
            "What could go wrong?",
          ].map((q) => (
            <button key={q} disabled={busy} onClick={() => void ask(q)}>
              {q}
            </button>
          ))}
        </div>
      )}
      <form
        className="ask-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (!question.trim() || question.length > 2000) {
            setError(
              errorMessage(
                new ApiError(
                  "INVALID_QUESTION",
                  "Enter a question between 1 and 2,000 characters.",
                  422,
                ),
              ),
            );
            return;
          }
          void ask(question);
        }}
      >
        <label
          className="sr-only"
          htmlFor={advanced ? "advanced-question" : "base-question"}
        >
          {advanced ? "Advanced review question" : "Base chat question"}
        </label>
        <input
          id={advanced ? "advanced-question" : "base-question"}
          value={question}
          maxLength={2000}
          placeholder={
            advanced ? "Challenge the evidence…" : "Ask about this pilot…"
          }
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button
          className="secondary"
          type="submit"
          disabled={busy || !question.trim()}
          aria-label={advanced ? "Ask advanced reviewer" : "Ask base chatbot"}
        >
          <ArrowUpRight size={18} />
        </button>
      </form>
      {busy && (
        <p role="status" className="small">
          {mock ? "Loading example response…" : "Checking supporting evidence…"}
        </p>
      )}
      {error && (
        <div className="error" role="alert">
          <span>{error}</span>
          {!!question.trim() && (
            <button className="text-button" onClick={() => void ask(question)}>
              Retry question
            </button>
          )}
        </div>
      )}
      {answer && (
        <div className="answer" role="status">
          <span className="eyebrow">
            {mock
              ? "SYNTHETIC EXAMPLE"
              : answer.status === "ok"
                ? "TOOL-BACKED ANSWER"
                : "INSUFFICIENT EVIDENCE"}
          </span>
          <p>{answer.answer}</p>
          {!mock && <details className="chat-method"><summary>How this answer was checked</summary><p className="small muted">Template-based reasoning over live MCP evidence. No language model is used by the base assistant.</p><p className="small muted">{answer.usage.tool_calls} tool calls · Audit {audit.audit_id}</p></details>}
          <div className="citations">
            {answer.supporting_evidence_ids.map((id) => (
              <button
                key={id}
                className="text-button"
                onClick={() => onEvidence(id)}
              >
                {id} <ArrowUpRight size={13} />
              </button>
            ))}
          </div>
          {answer.limitations.map((l) => (
            <p className="small muted" key={l}>
              {l}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
type ChatProps = {
  portfolio?: ModelState;
  api: DashboardApi;
  audit: Audit;
  mock: boolean;
  onEvidence: (id: string) => void;
};
type Turn = { id: string; question: string; answer?: Explanation; error?: string };

function Conversation({ api, audit, mock, onEvidence }: ChatProps) {
  const [draft, setDraft] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const sequence = useRef(0);
  const pending = useRef(false);
  const input = useRef<HTMLTextAreaElement>(null);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => () => { ++sequence.current; }, []);
  useEffect(() => { if (turns.length) end.current?.scrollIntoView?.({block:"nearest"}); }, [turns, busy]);

  async function send(text: string, retryId?: string) {
    const question = text.trim();
    if (!question || question.length > 2000 || pending.current) return;
    pending.current = true;
    const seq = ++sequence.current;
    const id = retryId ?? crypto.randomUUID();
    setBusy(true);
    if (retryId) setTurns(previous => previous.map(turn => turn.id === id ? { id, question } : turn));
    else { setTurns(previous => [...previous, { id, question }]); setDraft(""); }
    try {
      const request = {client_request_id:crypto.randomUUID(), question};
      const answer = assertRequestId(assertAuditId(await api.askBaseChat(audit.audit_id, request), audit.audit_id), request.client_request_id);
      if (seq === sequence.current) setTurns(previous => previous.map(turn => turn.id === id ? {...turn, answer} : turn));
    } catch (error) {
      if (seq === sequence.current) setTurns(previous => previous.map(turn => turn.id === id ? {...turn, error:errorMessage(error)} : turn));
    } finally {
      if (seq === sequence.current) { pending.current = false; setBusy(false); input.current?.focus(); }
    }
  }
  return <div className={`pilot-conversation ${turns.length ? "has-messages" : "is-empty"}`}>
    <header className="conversation-toolbar">
      <span>Pilot assistant <span className="conversation-mode">{mock ? "Synthetic demo" : "MCP"}</span></span>
      <button type="button" className="icon-button" aria-label="New chat" title="New chat" onClick={() => {
        ++sequence.current; pending.current = false; setBusy(false); setTurns([]); setDraft(""); input.current?.focus();
      }}><SquarePen size={19}/></button>
    </header>
    <div className="conversation-body">
      {!turns.length ? <div className="conversation-welcome"><h2>What would you like to know?</h2><p>Explore the CPU pilot with your data.</p></div> :
        <div className="conversation-messages" role="log" aria-label="Pilot conversation" aria-live="polite" aria-relevant="additions text">
          {turns.map(turn => <article className="conversation-turn" key={turn.id}>
            <div className="user-message"><span className="sr-only">You: </span>{turn.question}</div>
            <div className="assistant-message">
              <span className="assistant-avatar" aria-hidden="true"><Sparkles size={17}/></span>
              <div className="assistant-content"><span className="sr-only">Pilot assistant: </span>
                {turn.answer ? <>
                  {mock && <span className="conversation-answer-label">Synthetic example</span>}
                  {turn.answer.status !== "ok" && <span className="conversation-answer-label">Insufficient evidence</span>}
                  <p className="assistant-text">{turn.answer.answer}</p>
                  <div className="conversation-sources">{turn.answer.supporting_evidence_ids.map((id,index) => <button type="button" key={id} title={id} aria-label={mock ? id : `Open source ${index+1}`} onClick={() => onEvidence(id)}><BookOpen size={13}/>{`Source ${index+1}`}</button>)}</div>
                  <details className="conversation-method"><summary>Sources and limitations</summary><p>{mock ? "Synthetic example; no live tools were used." : "Template-based answers from live MCP evidence. Each question is checked independently."}</p><p>{turn.answer.usage.tool_calls} tool calls</p>{turn.answer.limitations.map(limit => <p key={limit}>{limit}</p>)}</details>
                </> : turn.error ? <div className="conversation-error" role="alert"><p>{turn.error}</p><button type="button" className="text-button" disabled={busy} onClick={() => void send(turn.question, turn.id)}>Retry question</button></div> : <div className="conversation-loading" role="status"><LoaderCircle size={16} aria-hidden="true"/>Checking evidence…</div>}
              </div>
            </div>
          </article>)}
          <div ref={end}/>
        </div>}
      <div className="conversation-compose-area">
        <form className="conversation-composer" onSubmit={event => {event.preventDefault(); void send(draft);}}>
          <label className="sr-only" htmlFor="pilot-message">Base chat question</label>
          <textarea id="pilot-message" ref={input} rows={1} maxLength={2000} placeholder="Ask about this pilot" value={draft} onChange={event => setDraft(event.target.value)} onKeyDown={event => {
            if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {event.preventDefault(); void send(draft);}
          }}/>
          <button type="submit" className="conversation-send" aria-label="Ask base chatbot" disabled={busy || !draft.trim()}>{busy ? <LoaderCircle size={19}/> : <ArrowUp size={20}/>}</button>
        </form>
        {!turns.length && <div className="conversation-suggestions">{["Why this pilot?", "Which jobs are eligible?", "What are the recovery assumptions?", "What could go wrong?"].map(question => <button key={question} type="button" onClick={() => void send(question)}>{question}</button>)}</div>}
        <p className="conversation-note">{mock ? "Synthetic demo · example responses" : "Answers grounded in pilot evidence · template-based"}</p>
      </div>
    </div>
  </div>;
}

export function ChatPanel(props: ChatProps) {
  const [scope,setScope]=useState(props.portfolio?.enabled?'simulation':'pilot');
  return (
    <section className="chat-workspace" id="ask">
      <h1 className="sr-only">Ask about this pilot</h1>
      {props.portfolio?.enabled&&<div className="review-scope-tabs" role="group" aria-label="Assistant scope"><button className="secondary" aria-pressed={scope==='simulation'} onClick={()=>setScope('simulation')}>Cost simulation review</button><button className="secondary" aria-pressed={scope==='pilot'} onClick={()=>setScope('pilot')}>Base pilot assistant</button></div>}
      {scope==='simulation'&&props.portfolio?.enabled?<SimulationReview model={props.portfolio}/>:<>
      <Conversation {...props}/>
      <details className="reviewer-disclosure chat-reviewer">
        <summary>Open optional advanced reviewer</summary>
        <QuestionPanel {...props} advanced />
      </details>
      </>}
    </section>
  );
}
