import React, { useState, useRef, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import {
  Sparkles,
  Send,
  User,
  Bot,
  FileText,
  ShieldCheck,
  ExternalLink,
  RotateCcw,
  Zap,
  Brain,
  Search,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  AlertTriangle,
  Paperclip,
  X,
  UploadCloud
} from 'lucide-react';
import { useGlossary } from '../context/GlossaryContext';

/* ─── Tiny Markdown renderer (no deps needed) ─── */
function renderMarkdown(text) {
  if (!text) return [];

  const lines = text.split('\n');
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // H3
    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={i} className="text-sm font-bold text-slate-800 mt-3 mb-1.5 leading-snug">
          {renderInline(line.slice(4))}
        </h3>
      );
      i++; continue;
    }
    // H2
    if (line.startsWith('## ')) {
      elements.push(
        <h2 key={i} className="text-sm font-bold text-teal-800 mt-3 mb-1.5 border-b border-teal-100 pb-1 leading-snug">
          {renderInline(line.slice(3))}
        </h2>
      );
      i++; continue;
    }
    // Blockquote
    if (line.startsWith('> ')) {
      elements.push(
        <blockquote key={i} className="border-l-2 border-amber-400 bg-amber-50 pl-3 pr-2 py-1.5 rounded-r-lg my-1.5 text-[11px] text-amber-800 italic">
          {renderInline(line.slice(2))}
        </blockquote>
      );
      i++; continue;
    }
    // Bullet list item
    if (line.match(/^[\-\*•] /)) {
      const bullets = [];
      while (i < lines.length && lines[i].match(/^[\-\*•] /)) {
        bullets.push(
          <li key={i} className="flex gap-1.5 items-start">
            <span className="text-teal-600 mt-0.5 shrink-0">•</span>
            <span>{renderInline(lines[i].slice(2))}</span>
          </li>
        );
        i++;
      }
      elements.push(<ul key={`ul-${i}`} className="space-y-1 my-1.5 text-[11.5px] text-slate-700">{bullets}</ul>);
      continue;
    }
    // Numbered list
    if (line.match(/^\d+\. /)) {
      const items = [];
      let num = 1;
      while (i < lines.length && lines[i].match(/^\d+\. /)) {
        items.push(
          <li key={i} className="flex gap-1.5 items-start">
            <span className="text-teal-700 font-semibold shrink-0 min-w-[1rem]">{num}.</span>
            <span>{renderInline(lines[i].replace(/^\d+\. /, ''))}</span>
          </li>
        );
        i++; num++;
      }
      elements.push(<ol key={`ol-${i}`} className="space-y-1 my-1.5 text-[11.5px] text-slate-700">{items}</ol>);
      continue;
    }
    // Horizontal rule
    if (line.match(/^---+$/)) {
      elements.push(<hr key={i} className="border-slate-200 my-2" />);
      i++; continue;
    }
    // Empty line → spacer
    if (line.trim() === '') {
      elements.push(<div key={i} className="h-1.5" />);
      i++; continue;
    }
    // Normal paragraph
    elements.push(
      <p key={i} className="text-[11.5px] text-slate-700 leading-relaxed">
        {renderInline(line)}
      </p>
    );
    i++;
  }

  return elements;
}

function renderInline(text) {
  if (!text) return null;
  // Split on **bold**, *italic*, `code`
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((part, idx) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={idx} className="font-semibold text-slate-800">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={idx} className="italic">{part.slice(1, -1)}</em>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={idx} className="px-1 py-0.5 bg-slate-100 text-teal-700 rounded text-[10px] font-mono">{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

/* ─── Typewriter Hook ─── */
function useTypewriter(text, enabled = true, speed = 6) {
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);
  const rafRef = useRef(null);
  const idxRef = useRef(0);

  useEffect(() => {
    if (!enabled || !text) {
      setDisplayed(text || '');
      setDone(true);
      return;
    }
    setDisplayed('');
    setDone(false);
    idxRef.current = 0;

    const tick = () => {
      idxRef.current = Math.min(idxRef.current + speed, text.length);
      setDisplayed(text.slice(0, idxRef.current));
      if (idxRef.current < text.length) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        setDone(true);
      }
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [text, enabled, speed]);

  return { displayed, done };
}

/* ─── Loading Phase Animation ─── */
const PHASES = [
  { icon: Search, label: 'Retrieving verified policy clauses…', color: 'text-blue-600' },
  { icon: Brain, label: 'Analysing IRDAI documents & facts…', color: 'text-violet-600' },
  { icon: Zap, label: 'Generating grounded response…', color: 'text-teal-600' },
];

function LoadingBubble({ seconds = 0 }) {
  const [phaseIdx, setPhaseIdx] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setPhaseIdx(p => (p + 1) % PHASES.length);
    }, 2200);
    return () => clearInterval(id);
  }, []);

  const Phase = PHASES[phaseIdx];
  const Icon = Phase.icon;
  const isColdStart = seconds >= 15;

  return (
    <div className="flex items-start gap-2.5 animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="w-7 h-7 rounded-xl bg-teal-700 text-white flex items-center justify-center shrink-0 shadow-sm">
        <Bot className="w-4 h-4" />
      </div>
      <div className="flex flex-col gap-1.5">
        <div className="px-4 py-3 rounded-2xl rounded-tl-xs bg-white border border-slate-200 shadow-xs flex items-center gap-2.5 min-w-[240px]">
          {/* Animated dots */}
          <div className="flex gap-1">
            {[0, 1, 2].map(d => (
              <div
                key={d}
                className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-bounce"
                style={{ animationDelay: `${d * 0.15}s`, animationDuration: '0.9s' }}
              />
            ))}
          </div>
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-slate-500">
            <Icon className={`w-3 h-3 ${Phase.color}`} />
            <span>{Phase.label}</span>
          </div>
          {/* Elapsed timer */}
          <span className="ml-auto text-[10px] text-slate-400 font-mono tabular-nums">
            {seconds}s
          </span>
        </div>
        {/* Cold-start hint — appears after 15s */}
        {isColdStart && (
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-200 text-[10px] text-amber-700 animate-in fade-in duration-300">
            <Zap className="w-3 h-3 shrink-0" />
            <span>BimaGyan AI is waking up from a cold start — this takes ~30–90s on first use. Subsequent queries are faster.</span>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Provider Badge ─── */
function ProviderBadge({ provider }) {
  if (!provider || provider === 'deterministic') return null;
  const map = {
    bimagyan: { label: 'BimaGyan AI', color: 'bg-teal-50 text-teal-800 border-teal-200' },
  };
  const cfg = map[provider] || { label: provider, color: 'bg-slate-50 text-slate-600 border-slate-200' };
  return (
    <span className={`inline-flex items-center gap-1 text-[9.5px] px-1.5 py-0.5 rounded-full border font-semibold ${cfg.color}`}>
      <Zap className="w-2.5 h-2.5" />
      {cfg.label}
    </span>
  );
}

/* ─── Copy Button ─── */
function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handle = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    });
  };
  return (
    <button
      onClick={handle}
      className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
      title="Copy response"
    >
      {copied ? <Check className="w-3 h-3 text-teal-600" /> : <Copy className="w-3 h-3" />}
    </button>
  );
}

/* ─── Citations Collapsible ─── */
function CitationsSection({ citations }) {
  const [open, setOpen] = useState(false);
  if (!citations || citations.length === 0) return null;
  return (
    <div className="pt-2 border-t border-slate-100">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 text-[10px] font-bold text-teal-700 uppercase tracking-wider hover:text-teal-900 transition-colors"
      >
        <FileText className="w-3 h-3" />
        {citations.length} Verified Source{citations.length > 1 ? 's' : ''} Cited
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>
      {open && (
        <div className="mt-2 space-y-1.5 animate-in fade-in slide-in-from-top-1 duration-200">
          {citations.map((c, cIdx) => (
            <div
              key={cIdx}
              className="p-2 rounded-lg bg-slate-50 border border-slate-200/80 text-[10.5px] text-slate-600 space-y-0.5"
            >
              <div className="flex items-center justify-between font-semibold text-slate-800">
                <span className="flex items-center gap-1 truncate max-w-[240px]">
                  <FileText className="w-2.5 h-2.5 text-teal-700 shrink-0" />
                  {c.title}{c.section ? ` — ${c.section}` : ''}
                </span>
                {c.source_url && (
                  <a
                    href={c.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-teal-700 hover:underline flex items-center gap-0.5 text-[9.5px] shrink-0"
                  >
                    Source <ExternalLink className="w-2.5 h-2.5" />
                  </a>
                )}
              </div>
              <p className="text-[10px] text-slate-500 italic line-clamp-2">"{c.snippet}"</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── Document Citations Collapsible ─── */
function DocumentCitationsSection({ citations, documentName }) {
  const [open, setOpen] = useState(false);
  if (!citations || citations.length === 0) return null;
  return (
    <div className="pt-2 border-t border-purple-100">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 text-[10px] font-bold text-purple-700 uppercase tracking-wider hover:text-purple-900 transition-colors cursor-pointer"
      >
        <FileText className="w-3 h-3 text-purple-600" />
        {citations.length} Document Clause{citations.length > 1 ? 's' : ''} Cited ({documentName})
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>
      {open && (
        <div className="mt-2 space-y-1.5 animate-in fade-in slide-in-from-top-1 duration-200">
          {citations.map((c, cIdx) => (
            <div
              key={cIdx}
              className="p-2 rounded-lg bg-purple-50/70 border border-purple-200 text-[10.5px] text-purple-950 space-y-1"
            >
              <div className="flex items-center justify-between font-semibold text-purple-900">
                <span className="flex items-center gap-1.5">
                  <span className="px-1.5 py-0.5 rounded bg-purple-200 text-purple-800 text-[9px] font-bold">
                    Page {c.page_number || 'N/A'}
                  </span>
                  <span className="text-purple-700 font-medium truncate max-w-[200px]">{documentName}</span>
                </span>
                {c.score !== undefined && c.score !== null && (
                  <span className="text-[9px] text-purple-600 font-mono">
                    Match: {Math.round(c.score * 100)}%
                  </span>
                )}
              </div>
              <p className="text-[10px] text-purple-900/90 italic leading-relaxed">
                "{c.snippet}"
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── Single Message Bubble ─── */
function MessageBubble({ message, isLatestAssistant }) {
  const isUser = message.role === 'user';
  const { displayed, done } = useTypewriter(
    isUser ? null : message.content,
    isLatestAssistant,
    8
  );

  const textToShow = isUser ? message.content : (isLatestAssistant ? displayed : message.content);

  return (
    <div
      className={`flex items-start gap-2.5 animate-in fade-in slide-in-from-bottom-2 duration-300 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div
        className={`w-7 h-7 rounded-xl flex items-center justify-center shrink-0 mt-0.5 shadow-sm ${
          isUser ? 'bg-slate-800 text-white' : 'bg-gradient-to-br from-teal-600 to-teal-800 text-white'
        }`}
      >
        {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
      </div>

      {/* Bubble */}
      <div
        className={`rounded-2xl max-w-[84%] space-y-2 ${
          isUser
            ? 'bg-slate-900 text-white px-4 py-3 rounded-tr-xs shadow-sm'
            : 'bg-white border border-slate-200/90 shadow-xs rounded-tl-xs px-4 py-3'
        }`}
      >
        {isUser ? (
          <div>
            {message.document_name && (
              <div className="inline-flex items-center gap-1.5 px-2 py-1 mb-1.5 rounded-lg bg-slate-800 border border-slate-700 text-purple-200 text-[10.5px]">
                <Paperclip className="w-3 h-3 text-purple-300" />
                <span className="font-medium truncate max-w-[200px]">{message.document_name}</span>
                {message.file_size && <span className="text-[9px] text-slate-400">({message.file_size})</span>}
              </div>
            )}
            <p className="text-[12px] text-white leading-relaxed">{message.content}</p>
          </div>
        ) : (
          <>
            {/* Header row: provider / document badge + copy */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 flex-wrap">
                {message.document_name ? (
                  <span className="inline-flex items-center gap-1 text-[9.5px] px-2 py-0.5 rounded-full bg-purple-50 text-purple-800 border border-purple-200 font-semibold">
                    <FileText className="w-2.5 h-2.5 text-purple-600" />
                    Grounded in {message.document_name}
                  </span>
                ) : (
                  message.provider_used && <ProviderBadge provider={message.provider_used} />
                )}
              </div>
              {done && <CopyButton text={message.content} />}
            </div>
            {/* Rendered markdown */}
            <div className="space-y-0.5">
              {renderMarkdown(textToShow)}
              {isLatestAssistant && !done && (
                <span className="inline-block w-0.5 h-3.5 bg-teal-500 animate-pulse ml-0.5 align-middle" />
              )}
            </div>
            {/* Citations — Global RAG or Document RAG */}
            {done && message.document_citations && (
              <DocumentCitationsSection
                citations={message.document_citations}
                documentName={message.document_name || 'Document'}
              />
            )}
            {done && message.citations && message.citations.length > 0 && (
              <CitationsSection citations={message.citations} />
            )}
            {/* Related terms */}
            {done && message.related_terms && message.related_terms.length > 0 && (
              <div className="pt-1.5 flex flex-wrap items-center gap-1.5">
                <span className="text-[9.5px] text-slate-400 font-medium">Related terms:</span>
                {message.related_terms.map((t, tIdx) => (
                  <button
                    key={tIdx}
                    onClick={() => message.onTermClick?.(t)}
                    className="text-[9.5px] font-medium px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200/60 hover:bg-teal-100 transition-colors cursor-pointer"
                  >
                    {t} ↗
                  </button>
                ))}
              </div>
            )}
            {/* Disclaimer */}
            {done && message.disclaimer && (
              <p className="text-[9.5px] text-slate-400 pt-1.5 border-t border-slate-100 leading-relaxed flex items-start gap-1">
                <AlertTriangle className="w-2.5 h-2.5 shrink-0 mt-0.5 text-slate-300" />
                {message.disclaimer}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/* ─── Main Page ─── */
export const AssistantPage = () => {
  const { openFullModal, findTerm } = useGlossary();

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Namaste! I'm **BimaGyan AI** — your grounded Indian insurance research assistant.\n\nI can explain complex policy clauses, compare plan wordings, decode waiting periods and exclusions, and answer regulatory questions — all backed by **verified IRDAI filings**.\n\nHow can I help you today?",
      citations: [],
      related_terms: ['Deductible', 'Co-payment', 'Room Rent Capping', 'Waiting Period'],
      provider_used: 'bimagyan',
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingSeconds, setLoadingSeconds] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const fileInputRef = useRef(null);
  const latestAssistantIdx = messages.filter(m => m.role === 'assistant').length - 1;

  const samplePrompts = [
    "Explain health insurance to me as a beginner.",
    "Difference between Cashless and Reimbursement claims?",
    "What exclusions should I check before buying?",
    "How does room rent capping work?",
    "What is PED waiting period in India?",
    "Why is term insurance better than endowment?",
  ];

  const documentPrompts = [
    "What are the waiting periods mentioned in this policy?",
    "Does this document cover modern robotic treatments?",
    "What are the room rent limits and co-pays?",
    "List all key exclusions or non-payable items.",
    "Summarize the claim filing procedure in this document.",
  ];

  const activePrompts = selectedFile ? documentPrompts : samplePrompts;

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, loading, scrollToBottom]);

  // Elapsed-seconds counter while loading (shows user the model isn't frozen)
  useEffect(() => {
    if (!loading) { setLoadingSeconds(0); return; }
    setLoadingSeconds(0);
    const id = setInterval(() => setLoadingSeconds(s => s + 1), 1000);
    return () => clearInterval(id);
  }, [loading]);

  // Warmup ping when page loads (fire-and-forget)
  useEffect(() => {
    fetch('/api/v1/assistant/warmup', { method: 'POST' }).catch(() => {});
  }, []);

  const handleSendMessage = async (queryText) => {
    const text = (queryText || inputQuery).trim();
    if (!text || loading) return;

    const currentFile = selectedFile;
    const userMsg = {
      role: 'user',
      content: text,
      document_name: currentFile ? currentFile.name : null,
      file_size: currentFile ? `${(currentFile.size / 1024).toFixed(1)} KB` : null,
    };
    setMessages(prev => [...prev, userMsg]);
    setInputQuery('');
    setLoading(true);
    inputRef.current?.focus();

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }));

      if (currentFile) {
        // ── TYPE 2 RAG: Document Grounded QA ──
        const response = await api.chatAssistantWithDocument(currentFile, text, history);
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: response.answer,
            document_name: response.document_name,
            total_pages: response.total_pages,
            document_citations: response.citations || [],
            provider_used: response.provider_used,
            disclaimer: response.disclaimer,
          }
        ]);
      } else {
        // ── TYPE 1 RAG: Platform Global Knowledge Base QA ──
        const response = await api.chatAssistant(text, history);

        const handleTermClick = (termName) => {
          const t = findTerm(termName);
          if (t) openFullModal(t);
        };

        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: response.answer,
            citations: response.citations || [],
            related_terms: response.related_glossary_terms || [],
            provider_used: response.provider_used,
            disclaimer: response.disclaimer,
            onTermClick: handleTermClick,
          }
        ]);
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `**Error processing request.** ${err.message}\n\nPlease try again in a moment.`,
          citations: [],
          provider_used: null,
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: "Chat cleared. What insurance question would you like to explore?",
        citations: [],
        provider_used: 'bimagyan',
      }
    ]);
  };

  let assistantMsgCounter = 0;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-5 flex flex-col h-full">
      {/* ── Header ── */}
      <div className="flex items-center justify-between py-3 border-b border-slate-200 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-teal-600 to-teal-800 text-white flex items-center justify-center shadow-sm">
            <Sparkles className="w-4 h-4 text-teal-100" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              BimaGyan AI Assistant
              <span className="text-[9px] px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 font-bold border border-teal-200 uppercase tracking-wide">
                IRDAI Grounded
              </span>
            </h1>
            <p className="text-[10.5px] text-slate-500">RAG over verified insurance filings · Not financial advice</p>
          </div>
        </div>
        <button
          onClick={handleClearChat}
          className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 text-[11px] flex items-center gap-1 transition-colors cursor-pointer"
          title="Clear chat"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline font-medium">Reset</span>
        </button>
      </div>

      {/* ── Suggested Prompts ── */}
      <div className="flex items-center gap-1.5 overflow-x-auto py-2 scrollbar-none shrink-0">
        <span className="text-slate-400 text-[10px] font-semibold whitespace-nowrap shrink-0">
          {selectedFile ? 'Doc queries:' : 'Try:'}
        </span>
        {activePrompts.map((prompt, idx) => (
          <button
            key={idx}
            disabled={loading}
            onClick={() => handleSendMessage(prompt)}
            className={`px-2.5 py-1 rounded-full border text-[10.5px] whitespace-nowrap transition-all shadow-2xs cursor-pointer disabled:opacity-50 font-medium ${
              selectedFile
                ? 'bg-purple-50/80 border-purple-200 text-purple-700 hover:bg-purple-100 hover:border-purple-300'
                : 'bg-white border-slate-200 hover:border-teal-500 hover:text-teal-800 hover:bg-teal-50/50 text-slate-600'
            }`}
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-3 pr-0.5">
        {messages.map((m, idx) => {
          const isAssistant = m.role === 'assistant';
          const currentAssistantIdx = isAssistant ? assistantMsgCounter++ : -1;
          const isLatest = isAssistant && currentAssistantIdx === latestAssistantIdx;

          return (
            <MessageBubble
              key={idx}
              message={m}
              isLatestAssistant={isLatest}
            />
          );
        })}

        {loading && <LoadingBubble seconds={loadingSeconds} />}
        <div ref={messagesEndRef} />
      </div>

      {/* ── Input ── */}
      <div className="shrink-0 py-2.5 border-t border-slate-200/80">
        {/* Selected Document Chip (Type 2 RAG) */}
        {selectedFile && (
          <div className="flex items-center justify-between px-3 py-1.5 mb-2 rounded-xl bg-purple-50 border border-purple-200 text-purple-900 text-[11px] animate-in fade-in duration-200">
            <div className="flex items-center gap-2 truncate">
              <div className="w-5 h-5 rounded-md bg-purple-600 text-white flex items-center justify-center shrink-0">
                <FileText className="w-3 h-3" />
              </div>
              <span className="font-semibold truncate max-w-[280px]">{selectedFile.name}</span>
              <span className="text-[10px] text-purple-600 font-mono">
                ({(selectedFile.size / 1024).toFixed(1)} KB)
              </span>
              <span className="px-2 py-0.5 rounded-full bg-purple-200 text-purple-800 text-[9px] font-bold uppercase tracking-wider">
                Doc RAG Mode
              </span>
            </div>
            <button
              onClick={() => {
                setSelectedFile(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
              }}
              className="p-1 text-purple-400 hover:text-purple-700 hover:bg-purple-100 rounded-md transition-colors cursor-pointer"
              title="Remove document"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        <div className="relative flex items-end gap-2">
          {/* Hidden File Input */}
          <input
            type="file"
            ref={fileInputRef}
            accept=".pdf,.docx,.txt,.md"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                setSelectedFile(e.target.files[0]);
              }
            }}
          />

          {/* Upload Button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading}
            className={`shrink-0 p-2.5 rounded-xl border transition-all cursor-pointer ${
              selectedFile
                ? 'bg-purple-100 border-purple-300 text-purple-700 hover:bg-purple-200'
                : 'bg-white border-slate-300 text-slate-500 hover:text-teal-700 hover:border-teal-400 hover:bg-teal-50/50'
            }`}
            title={selectedFile ? `Attached: ${selectedFile.name} (Click to change)` : "Upload document (PDF, DOCX, TXT) for Document RAG analysis"}
            aria-label="Upload document"
          >
            <Paperclip className="w-4 h-4" />
          </button>

          <textarea
            ref={inputRef}
            rows={1}
            placeholder={
              selectedFile
                ? `Ask about ${selectedFile.name} (e.g. 'What are the waiting periods?', 'Is robotic surgery covered?')...`
                : "Ask about Indian insurance (e.g. 'What is room rent capping?', 'Compare Optima Secure vs Care Supreme')…"
            }
            value={inputQuery}
            onChange={(e) => {
              setInputQuery(e.target.value);
              // Auto-grow
              e.target.style.height = 'auto';
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
            }}
            onKeyDown={handleKeyDown}
            disabled={loading}
            className={`flex-1 pl-4 pr-4 py-2.5 bg-white rounded-2xl border text-[12px] text-slate-800 focus:outline-none focus:ring-2 placeholder-slate-400 shadow-xs resize-none overflow-hidden transition-all leading-relaxed disabled:opacity-60 ${
              selectedFile
                ? 'border-purple-300 focus:border-purple-500 focus:ring-purple-500/20'
                : 'border-slate-300 focus:border-teal-500 focus:ring-teal-500/20'
            }`}
            style={{ minHeight: '42px', maxHeight: '120px' }}
          />

          <button
            onClick={() => handleSendMessage()}
            disabled={!inputQuery.trim() || loading}
            className={`shrink-0 p-2.5 rounded-xl active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-all shadow-sm cursor-pointer ${
              selectedFile
                ? 'bg-purple-700 hover:bg-purple-800'
                : 'bg-teal-700 hover:bg-teal-800'
            }`}
            aria-label="Send question"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>

        <div className="text-[9.5px] text-slate-400 text-center mt-1.5 flex items-center justify-center gap-1">
          <ShieldCheck className="w-2.5 h-2.5 text-teal-500 shrink-0" />
          <span>
            {selectedFile
              ? `Document RAG Active: Questions grounded strictly in ${selectedFile.name}`
              : "Grounded in official IRDAI public filings · Educational only, not licensed financial advice · Press Enter to send"}
          </span>
        </div>
      </div>
    </div>
  );
};
