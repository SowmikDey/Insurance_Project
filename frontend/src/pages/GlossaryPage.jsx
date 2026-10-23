import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../services/api';
import { 
  HelpCircle, 
  Search, 
  BookOpen, 
  IndianRupee, 
  TrendingUp, 
  ShieldAlert, 
  AlertCircle,
  ExternalLink,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export const GlossaryPage = () => {
  const { termSlug } = useParams();

  const [terms, setTerms] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedSlugs, setExpandedSlugs] = useState(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTerms = async () => {
      setLoading(true);
      try {
        const data = await api.getGlossaryTerms();
        setTerms(data);
        if (termSlug) {
          setExpandedSlugs(new Set([termSlug]));
        }
      } catch (err) {
        console.error('Failed to load glossary dictionary:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchTerms();
  }, [termSlug]);

  const toggleExpand = (slug) => {
    setExpandedSlugs(prev => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  };

  const categories = ['all', 'Health', 'Health & Motor', 'Motor', 'General', 'Claims'];

  const filteredTerms = terms.filter(t => {
    const matchesCat = selectedCategory === 'all' || t.category.toLowerCase().includes(selectedCategory.toLowerCase());
    const matchesSearch = !searchQuery || 
      t.term.toLowerCase().includes(searchQuery.toLowerCase()) || 
      t.what_does_it_mean.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-50 text-teal-800 text-xs font-semibold border border-teal-200">
          <BookOpen className="w-3.5 h-3.5" />
          <span>Inspired by Zerodha Varsity</span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
          Interactive Insurance Glossary
        </h1>
        <p className="text-sm text-slate-600 leading-relaxed font-normal">
          Every insurance term broken down into 5 critical dimensions: meaning, practical importance, exact INR financial impact, trade-offs, and fine-print traps.
        </p>

        {/* Search Input */}
        <div className="pt-3 max-w-md mx-auto relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search any term (e.g., Deductible, Co-payment, Room Rent)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 bg-white rounded-xl border border-slate-300 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-700 shadow-xs placeholder-slate-400"
          />
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex items-center justify-center gap-2 flex-wrap">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${
              selectedCategory === cat
                ? 'bg-teal-800 text-white shadow-xs'
                : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
            }`}
          >
            {cat === 'all' ? 'All Concepts' : cat}
          </button>
        ))}
      </div>

      {/* Terms Accordion List */}
      {loading ? (
        <div className="py-20 text-center">
          <div className="w-8 h-8 border-2 border-teal-700 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-xs text-slate-500">Loading glossary terms...</p>
        </div>
      ) : filteredTerms.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 text-xs text-slate-500">
          No glossary terms match your search query.
        </div>
      ) : (
        <div className="space-y-4">
          {filteredTerms.map((t) => {
            const isExpanded = expandedSlugs.has(t.slug);

            return (
              <div
                key={t.slug}
                id={t.slug}
                className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden transition-all"
              >
                {/* Term Header Banner */}
                <div
                  onClick={() => toggleExpand(t.slug)}
                  className="p-5 flex items-center justify-between cursor-pointer hover:bg-slate-50/70 transition-colors"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-slate-900">{t.term}</h3>
                      <span className="text-[10px] font-semibold px-2 py-0.2 rounded-full bg-teal-50 text-teal-800 border border-teal-200">
                        {t.category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 line-clamp-1">
                      {t.what_does_it_mean}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-xs text-teal-800 font-semibold hidden sm:inline">
                      {isExpanded ? 'Collapse' : 'Expand 5-Pillar Card'}
                    </span>
                    {isExpanded ? (
                      <ChevronUp className="w-5 h-5 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-slate-400" />
                    )}
                  </div>
                </div>

                {/* 5-Pillars Card Body */}
                {isExpanded && (
                  <div className="px-5 pb-6 pt-2 border-t border-slate-100 space-y-4 text-xs leading-relaxed animate-in fade-in duration-150">
                    {/* 1. What it means */}
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100 space-y-1">
                      <span className="font-bold text-teal-900 uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                        <HelpCircle className="w-3.5 h-3.5 text-teal-700" /> 1. What does it mean?
                      </span>
                      <p className="text-slate-700">{t.what_does_it_mean}</p>
                    </div>

                    {/* 2. Why it matters */}
                    <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-100 space-y-1">
                      <span className="font-bold text-indigo-900 uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                        <AlertCircle className="w-3.5 h-3.5 text-indigo-700" /> 2. Why does it matter to you?
                      </span>
                      <p className="text-slate-700">{t.why_does_it_matter}</p>
                    </div>

                    {/* 3. Financial impact (INR example) */}
                    <div className="p-3.5 bg-amber-50/70 rounded-xl border border-amber-200/80 space-y-1">
                      <span className="font-bold text-amber-950 uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                        <IndianRupee className="w-3.5 h-3.5 text-amber-700" /> 3. How does it affect your money? (Numerical Example)
                      </span>
                      <p className="text-amber-950/90">{t.financial_impact_example}</p>
                    </div>

                    {/* 4. Trade-off analysis */}
                    <div className="p-3.5 bg-emerald-50/70 rounded-xl border border-emerald-200/80 space-y-1">
                      <span className="font-bold text-emerald-950 uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                        <TrendingUp className="w-3.5 h-3.5 text-emerald-700" /> 4. Is a higher or lower value better?
                      </span>
                      <p className="text-emerald-950/90">{t.trade_off_analysis}</p>
                    </div>

                    {/* 5. Watch out tips */}
                    <div className="p-3.5 bg-rose-50/70 rounded-xl border border-rose-200/80 space-y-1">
                      <span className="font-bold text-rose-950 uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                        <ShieldAlert className="w-3.5 h-3.5 text-rose-700" /> 5. What should you watch out for? (Traps & Fine Print)
                      </span>
                      <p className="text-rose-950/90">{t.watch_out_tips}</p>
                    </div>

                    {/* Related Module Footer */}
                    {t.related_module_slug && (
                      <div className="pt-2 flex justify-end">
                        <Link
                          to={`/learn/${t.related_module_slug}`}
                          className="text-xs font-semibold text-teal-800 hover:underline flex items-center gap-1"
                        >
                          Deep-dive in Module <ExternalLink className="w-3 h-3" />
                        </Link>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
