import { useEffect, useRef, useState } from "react";
import { MessageSquare, Sparkles, ArrowUpRight } from "lucide-react";
import type { Audit, DashboardApi, Explanation } from "../api/types";
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
export function ChatPanel(props: {
  api: DashboardApi;
  audit: Audit;
  mock: boolean;
  onEvidence: (id: string) => void;
}) {
  return (
    <section className="panel" id="ask">
      <div className="section-heading">
        <div>
          <span className="eyebrow">UNDERSTAND THE DECISION</span>
          <h2>Ask about this pilot</h2>
        </div>
        <MessageSquare size={20} />
      </div>
      <QuestionPanel {...props} advanced={false} />
      <details className="reviewer-disclosure">
        <summary>Open optional advanced reviewer</summary>
        <QuestionPanel {...props} advanced />
      </details>
    </section>
  );
}
