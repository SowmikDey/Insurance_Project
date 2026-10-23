import React, { useState, useRef, useEffect } from 'react';
import { api } from '../services/api';
import { 
  Sparkles, 
  Send, 
  User, 
  Bot, 
  FileText, 
  ShieldCheck, 
  ExternalLink, 
  HelpCircle,
  AlertTriangle,
  RotateCcw
} from 'lucide-react';
import { HighlightedText } from '../components/HighlightedText';
import { useGlossary } from '../context/GlossaryContext';

export const AssistantPage = () => {
  const { openFullModal, findTerm } = useGlossary();

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Namaste! I am your AI Insurance Guide for India. I can explain complex terminology, compare policy wordings, and break down waiting periods and exclusions using verified IRDAI prospectus documents. How can I help you today?",
      citations: [],
      related_terms: ['Deductible', 'Co-payment', 'Room Rent Capping', 'Waiting Period']
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const samplePrompts = [
    "Explain health insurance to me like I am a beginner.",
    "What is the difference between Cashless and Reimbursement claims?",
    "Which exclusions should I pay attention to before buying?",
    "Explain how room rent capping leads to proportionate deductions.",
    "What is the waiting period for pre-existing diseases in India?",
    "Why is pure term insurance better than an endowment policy?"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (queryText) => {
    const text = queryText || inputQuery;
    if (!text.trim() || loading) return;

    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInputQuery('');
    setLoading(true);

    try {
      // Build history
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const response = await api.chatAssistant(text, history);

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: response.answer,
          citations: response.citations || [],
          related_terms: response.related_glossary_terms || [],
          disclaimer: response.disclaimer
        }
      ]);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `I encountered an issue connecting to the document retrieval service: ${err.message}. Please try asking your question again.`,
          citations: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleTermClick = (termName) => {
    const t = findTerm(termName);
    if (t) openFullModal(t);
  };

  const handleClearChat = () => {
    setMessages([
      {
        role: 'assistant',
        content: "Chat cleared. What insurance question would you like to explore?",
        citations: []
      }
    ]);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6 flex flex-col h-[calc(100vh-8rem)]">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-teal-800 text-white flex items-center justify-center shadow-xs">
            <Sparkles className="w-4.5 h-4.5 text-teal-200" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900 flex items-center gap-2">
              AI Insurance Assistant
              <span className="text-[10px] px-2 py-0.2 rounded-full bg-teal-50 text-teal-800 font-bold border border-teal-200">
                Grounded in IRDAI Filings
              </span>
            </h1>
            <p className="text-[11px] text-slate-500">Retrieval-Augmented Generation (RAG) with Verified Citations</p>
          </div>
        </div>

        <button
          onClick={handleClearChat}
          className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 text-xs flex items-center gap-1 cursor-pointer"
          title="Clear chat"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Reset</span>
        </button>
      </div>

      {/* Suggested Questions Pills (Shrink-0) */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none shrink-0 text-xs">
        <span className="text-slate-400 font-medium text-[11px] whitespace-nowrap">Suggested:</span>
        {samplePrompts.map((prompt, idx) => (
          <button
            key={idx}
            disabled={loading}
            onClick={() => handleSendMessage(prompt)}
            className="px-3 py-1.5 rounded-full bg-white border border-slate-200 hover:border-teal-600 hover:text-teal-800 text-slate-600 text-xs whitespace-nowrap transition-all shadow-2xs cursor-pointer"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.map((m, idx) => {
          const isUser = m.role === 'user';
          return (
            <div
              key={idx}
              className={`flex items-start gap-3 text-xs leading-relaxed ${
                isUser ? 'flex-row-reverse' : ''
              }`}
            >
              <div
                className={`w-7 h-7 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${
                  isUser ? 'bg-slate-800 text-white' : 'bg-teal-700 text-white'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`p-4 rounded-2xl max-w-[85%] space-y-3 ${
                  isUser
                    ? 'bg-slate-900 text-white rounded-tr-xs'
                    : 'bg-white border border-slate-200/90 text-slate-800 shadow-xs rounded-tl-xs'
                }`}
              >
                <div className="whitespace-pre-wrap leading-relaxed text-xs">
                  {isUser ? m.content : <HighlightedText text={m.content} />}
                </div>

                {/* Grounded Citations Box */}
                {!isUser && m.citations && m.citations.length > 0 && (
                  <div className="pt-2 border-t border-slate-100 space-y-1.5">
                    <span className="font-bold text-[10px] text-teal-800 uppercase tracking-wider block">
                      Verified Policy & IRDAI Sources Cited:
                    </span>
                    <div className="space-y-1.5">
                      {m.citations.map((c, cIdx) => (
                        <div
                          key={cIdx}
                          className="p-2 rounded-lg bg-slate-50 border border-slate-200/80 text-[11px] text-slate-600 space-y-0.5"
                        >
                          <div className="flex items-center justify-between font-semibold text-slate-800">
                            <span className="flex items-center gap-1">
                              <FileText className="w-3 h-3 text-teal-700 shrink-0" />
                              {c.title} {c.section ? `— ${c.section}` : ''}
                            </span>
                            {c.source_url && (
                              <a
                                href={c.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-teal-700 hover:underline flex items-center gap-0.5 text-[10px]"
                              >
                                Source <ExternalLink className="w-2.5 h-2.5" />
                              </a>
                            )}
                          </div>
                          <p className="text-[10px] text-slate-500 italic">"{c.snippet}"</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Related Glossary Pills */}
                {!isUser && m.related_terms && m.related_terms.length > 0 && (
                  <div className="pt-2 flex flex-wrap items-center gap-1.5">
                    <span className="text-[10px] text-slate-400">Related terms:</span>
                    {m.related_terms.map((t, tIdx) => (
                      <button
                        key={tIdx}
                        onClick={() => handleTermClick(t)}
                        className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-teal-50 text-teal-800 border border-teal-200/60 hover:bg-teal-100 transition-colors cursor-pointer"
                      >
                        {t} ↗
                      </button>
                    ))}
                  </div>
                )}

                {/* Disclaimer */}
                {!isUser && m.disclaimer && (
                  <p className="text-[9px] text-slate-400 pt-1 border-t border-slate-50">
                    {m.disclaimer}
                  </p>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex items-start gap-3 text-xs">
            <div className="w-7 h-7 rounded-xl bg-teal-700 text-white flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-4 rounded-2xl bg-white border border-slate-200 text-slate-600 rounded-tl-xs flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-teal-700 border-t-transparent rounded-full animate-spin" />
              <span>Searching verified policy clauses & IRDAI circulars...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box (Shrink-0) */}
      <div className="shrink-0 pt-2">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="relative flex items-center"
        >
          <input
            type="text"
            placeholder="Ask anything about Indian insurance (e.g., 'What is room rent capping?', 'Compare Optima Secure vs Care Supreme')..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={loading}
            className="w-full pl-4 pr-12 py-3 bg-white rounded-2xl border border-slate-300 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-700 placeholder-slate-400 shadow-xs"
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || loading}
            className="absolute right-2 p-2 rounded-xl bg-teal-800 hover:bg-teal-900 disabled:opacity-40 text-white transition-colors cursor-pointer"
            aria-label="Send question"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
        <div className="text-[10px] text-slate-400 text-center mt-1.5 flex items-center justify-center gap-1">
          <ShieldCheck className="w-3 h-3 text-teal-600" />
          <span>Grounded in official IRDAI public filings. Educational support only, not licensed financial advice.</span>
        </div>
      </div>
    </div>
  );
};
