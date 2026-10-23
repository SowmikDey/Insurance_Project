import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGlossary } from '../context/GlossaryContext';
import { X, BookOpen, AlertCircle, HelpCircle, TrendingUp, IndianRupee, ShieldAlert, ExternalLink } from 'lucide-react';

export const GlossaryModal = () => {
  const { modalTerm, closeModal } = useGlossary();
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') closeModal();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [closeModal]);

  if (!modalTerm) return null;

  const navigateToModule = (slug) => {
    closeModal();
    navigate(`/learn/${slug}`);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-150">
      <div 
        className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col animate-in zoom-in-95 duration-150"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-term-title"
      >
        {/* Header */}
        <div className="px-6 py-4.5 bg-slate-50/80 border-b border-slate-200/80 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-100/80 text-teal-800 flex items-center justify-center">
              <BookOpen className="w-4.5 h-4.5 text-teal-700" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 id="modal-term-title" className="text-lg font-bold text-slate-800">
                  {modalTerm.term}
                </h3>
                <span className="text-xs px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200 font-medium">
                  {modalTerm.category}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">Zerodha Varsity-style Contextual Concept Card</p>
            </div>
          </div>
          <button
            onClick={closeModal}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors cursor-pointer"
            aria-label="Close card"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 5 Pillars Content */}
        <div className="p-6 overflow-y-auto space-y-5 text-sm leading-relaxed">
          {/* 1. What does it mean? */}
          <section className="bg-slate-50/60 p-4 rounded-xl border border-slate-100">
            <div className="flex items-center gap-2 mb-1.5 text-teal-900 font-semibold text-xs tracking-wider uppercase">
              <HelpCircle className="w-4 h-4 text-teal-700" />
              1. What does it mean?
            </div>
            <p className="text-slate-700 leading-relaxed font-normal">
              {modalTerm.what_does_it_mean}
            </p>
          </section>

          {/* 2. Why does it matter? */}
          <section className="bg-slate-50/60 p-4 rounded-xl border border-slate-100">
            <div className="flex items-center gap-2 mb-1.5 text-indigo-900 font-semibold text-xs tracking-wider uppercase">
              <AlertCircle className="w-4 h-4 text-indigo-600" />
              2. Why does it matter to you?
            </div>
            <p className="text-slate-700 leading-relaxed">
              {modalTerm.why_does_it_matter}
            </p>
          </section>

          {/* 3. How does it affect your money? */}
          <section className="bg-amber-50/60 p-4 rounded-xl border border-amber-200/70">
            <div className="flex items-center gap-2 mb-1.5 text-amber-900 font-semibold text-xs tracking-wider uppercase">
              <IndianRupee className="w-4 h-4 text-amber-700" />
              3. How does it affect your money? (Numerical Example)
            </div>
            <p className="text-amber-950/90 leading-relaxed">
              {modalTerm.financial_impact_example}
            </p>
          </section>

          {/* 4. Is higher or lower better? */}
          <section className="bg-emerald-50/60 p-4 rounded-xl border border-emerald-200/70">
            <div className="flex items-center gap-2 mb-1.5 text-emerald-900 font-semibold text-xs tracking-wider uppercase">
              <TrendingUp className="w-4 h-4 text-emerald-700" />
              4. Is a higher or lower value better? (Trade-offs)
            </div>
            <p className="text-emerald-950/90 leading-relaxed">
              {modalTerm.trade_off_analysis}
            </p>
          </section>

          {/* 5. What should you watch out for? */}
          <section className="bg-rose-50/60 p-4 rounded-xl border border-rose-200/70">
            <div className="flex items-center gap-2 mb-1.5 text-rose-900 font-semibold text-xs tracking-wider uppercase">
              <ShieldAlert className="w-4 h-4 text-rose-700" />
              5. What should you watch out for? (Caveats & Traps)
            </div>
            <p className="text-rose-950/90 leading-relaxed">
              {modalTerm.watch_out_tips}
            </p>
          </section>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <span className="text-[11px] text-slate-500">
            Source: {modalTerm.official_reference_source || 'IRDAI Master Circulars'}
          </span>
          <div className="flex items-center gap-2">
            {modalTerm.related_module_slug && (
              <button
                onClick={() => navigateToModule(modalTerm.related_module_slug)}
                className="px-3.5 py-1.5 rounded-lg bg-teal-700 hover:bg-teal-800 text-white text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer shadow-xs"
              >
                Learn in Deep Module <ExternalLink className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={closeModal}
              className="px-3.5 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-medium transition-colors cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
