import React from 'react';
import { useGlossary } from '../context/GlossaryContext';
import { ExternalLink, HelpCircle, ArrowRight } from 'lucide-react';

export const GlossaryPopover = () => {
  const { activeTerm, popoverPos, handleMouseEnter, handleMouseLeave, openFullModal } = useGlossary();

  if (!activeTerm) return null;

  return (
    <div
      role="tooltip"
      aria-live="polite"
      className="fixed z-50 w-88 bg-white rounded-xl shadow-xl border border-slate-200 p-4 transition-all duration-200 animate-in fade-in zoom-in-95"
      style={{
        top: `${popoverPos.top}px`,
        left: `${popoverPos.left}px`,
      }}
      onMouseEnter={() => {
        // Keep popover open while hovering directly inside it
        handleMouseEnter(activeTerm.slug, { currentTarget: { getBoundingClientRect: () => ({ left: popoverPos.left, bottom: popoverPos.top - 8 }) } });
      }}
      onMouseLeave={handleMouseLeave}
    >
      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
        <div className="flex items-center gap-1.5">
          <HelpCircle className="w-4 h-4 text-teal-700" />
          <h4 className="font-semibold text-slate-800 text-sm tracking-tight">{activeTerm.term}</h4>
        </div>
        <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-teal-50 text-teal-800 border border-teal-200/60">
          {activeTerm.category}
        </span>
      </div>

      <div className="mt-2.5 space-y-2 text-xs">
        <div>
          <span className="font-semibold text-slate-700 block mb-0.5">What it means:</span>
          <p className="text-slate-600 leading-relaxed line-clamp-3">
            {activeTerm.what_does_it_mean}
          </p>
        </div>

        {activeTerm.financial_impact_example && (
          <div className="bg-amber-50/70 border border-amber-200/80 rounded-lg p-2.5 mt-2">
            <span className="font-semibold text-amber-900 block mb-0.5 flex items-center gap-1">
              💰 How it affects your money:
            </span>
            <p className="text-amber-950/80 text-[11px] leading-relaxed line-clamp-2">
              {activeTerm.financial_impact_example}
            </p>
          </div>
        )}
      </div>

      <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between">
        <button
          onClick={() => openFullModal(activeTerm)}
          className="text-xs font-medium text-teal-700 hover:text-teal-800 flex items-center gap-1 transition-colors cursor-pointer"
        >
          View 5-Point Varsity Breakdown <ArrowRight className="w-3.5 h-3.5" />
        </button>
        <span className="text-[10px] text-slate-400">Click term to pin</span>
      </div>
    </div>
  );
};
