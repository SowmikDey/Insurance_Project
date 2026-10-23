import React from 'react';
import { Link } from 'react-router-dom';
import { 
  BookOpen, 
  Compass, 
  ArrowRight, 
  ShieldCheck, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle, 
  TrendingUp, 
  Award,
  HelpCircle
} from 'lucide-react';
import { useGlossary } from '../context/GlossaryContext';

export const HomePage = () => {
  const { openFullModal, findTerm } = useGlossary();

  const handleOpenGlossarySample = (termName) => {
    const term = findTerm(termName);
    if (term) openFullModal(term);
  };

  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-white border-b border-slate-200/80 pt-12 pb-16 lg:pt-18 lg:pb-22">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto space-y-5">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 border border-teal-200/70 text-teal-800 text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5 text-teal-600" />
              <span>Free, 100% Unbiased Insurance Platform for India</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight">
              Understand and choose insurance <span className="text-teal-700 underline decoration-teal-300 decoration-wavy decoration-2">without the confusion</span>.
            </h1>

            <p className="text-base sm:text-lg text-slate-600 leading-relaxed font-normal max-w-2xl mx-auto">
              No sales pitches, no spam calls, and no opaque fine print. Learn insurance concepts from scratch, explore authentic policies, and ask our AI assistant grounded in official documentation.
            </p>

            {/* Dual Journey Buttons (Option A vs Option B) */}
            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/learn"
                className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-teal-800 hover:bg-teal-900 text-white font-semibold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 group cursor-pointer"
              >
                <BookOpen className="w-4 h-4 text-teal-200 group-hover:scale-110 transition-transform" />
                <span>Option A: Learn About Insurance</span>
                <span className="text-[10px] bg-teal-700/80 px-2 py-0.5 rounded-full uppercase tracking-wider font-bold">Free Modules</span>
              </Link>

              <Link
                to="/explore"
                className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-slate-100 hover:bg-slate-200/80 text-slate-800 font-semibold text-sm border border-slate-300 transition-all flex items-center justify-center gap-2 group cursor-pointer"
              >
                <Compass className="w-4 h-4 text-slate-600 group-hover:rotate-45 transition-transform" />
                <span>Option B: Explore Policies Directly</span>
                <ArrowRight className="w-4 h-4 text-slate-500 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>

            {/* Interactive Concept Teaser Bar */}
            <div className="pt-6 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-500">
              <span className="flex items-center gap-1 font-medium text-slate-600">
                <HelpCircle className="w-3.5 h-3.5 text-teal-600" />
                Try Varsity Concept Cards:
              </span>
              {['Deductible', 'Co-payment', 'Room Rent Capping', 'Waiting Period', 'Restoration Benefit'].map((term) => (
                <button
                  key={term}
                  onClick={() => handleOpenGlossarySample(term)}
                  className="px-2.5 py-1 rounded-lg bg-slate-50 hover:bg-teal-50 text-teal-800 font-medium border border-slate-200/80 hover:border-teal-300 transition-all cursor-pointer"
                >
                  {term} ↗
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* The Core Problem & How We Fix It */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-10">
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
            Why Buying Insurance in India is Broken
          </h2>
          <p className="text-sm text-slate-600 mt-2">
            Most first-time buyers are sold products they don't understand, only to face massive claim rejections later.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
            <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-700 flex items-center justify-center mb-4">
              <AlertCircle className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-2">Hidden Room Rent Traps</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Insurers slip in a 1% room rent cap. If you pick a slightly nicer room, proportionate deductions cut your entire surgery and doctor fees by 50%.
            </p>
            <div className="mt-4 pt-3 border-t border-slate-100 text-teal-700 text-xs font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> BimaGyan flags all room rent clauses clearly
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center mb-4">
              <HelpCircle className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-2">Misleading Agent Promises</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Agents tell you 'everything is covered from day 1' or encourage hiding diabetes on application forms, leading to 100% claim rejection upon hospitalization.
            </p>
            <div className="mt-4 pt-3 border-t border-slate-100 text-teal-700 text-xs font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> We explain 3-stage waiting periods honestly
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center mb-4">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-2">Terrible Endowment Schemes</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Millions buy ULIPs and money-back plans yielding barely 4-5% return while providing dangerously inadequate life coverage for their family.
            </p>
            <div className="mt-4 pt-3 border-t border-slate-100 text-teal-700 text-xs font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> We teach why Pure Term + Mutual Funds wins
            </div>
          </div>
        </div>
      </section>

      {/* Two Exploration Paths Preview */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Path A Box */}
          <div className="bg-gradient-to-br from-teal-900 to-teal-950 text-white p-8 rounded-3xl shadow-lg relative overflow-hidden flex flex-col justify-between">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-800/80 text-teal-200 text-xs font-semibold">
                <BookOpen className="w-3.5 h-3.5" />
                <span>Option A: Education First</span>
              </div>
              <h3 className="text-2xl font-bold tracking-tight">
                Learn Insurance From the Ground Up
              </h3>
              <p className="text-sm text-teal-100/90 leading-relaxed font-normal">
                Structured like Zerodha Varsity. 10 bite-sized modules starting from "What is Insurance" to filing claims and spotting deceptive bank selling tactics. Complete with real-world Indian examples and interactive quizzes.
              </p>
              <ul className="space-y-2 text-xs text-teal-200/90 pt-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
                  <span>100% Free forever, no registration needed</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
                  <span>Interactive quizzes with explanatory feedback</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
                  <span>Track your learning progress as you go</span>
                </li>
              </ul>
            </div>

            <div className="pt-8">
              <Link
                to="/learn"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-white text-teal-950 font-bold text-xs hover:bg-teal-50 transition-colors shadow-md"
              >
                <span>Start Learning Now</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Path B Box */}
          <div className="bg-white border border-slate-200 p-8 rounded-3xl shadow-xs flex flex-col justify-between">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 text-slate-800 text-xs font-semibold">
                <Compass className="w-3.5 h-3.5 text-teal-700" />
                <span>Option B: Direct Exploration</span>
              </div>
              <h3 className="text-2xl font-bold text-slate-900 tracking-tight">
                Explore & Compare Policies Directly
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed font-normal">
                Already know what you need? Dive straight into India's top health, term life, and motor insurance plans. Filter by room rent rules, co-pays, budget, and CSR, and compare up to 4 policies side-by-side.
              </p>
              <ul className="space-y-2 text-xs text-slate-600 pt-2">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-700 shrink-0" />
                  <span>Grounded in verified IRDAI public prospectuses</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-700 shrink-0" />
                  <span>Interactive hover definitions on every tricky clause</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-teal-700 shrink-0" />
                  <span>Clear policy benefits, limitations, and waiting period breakdowns</span>
                </li>
              </ul>
            </div>

            <div className="pt-8">
              <Link
                to="/explore"
                className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-slate-900 hover:bg-slate-850 text-white font-bold text-xs transition-colors shadow-md"
              >
                <span>Browse Policy Database</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Categories Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900">Supported Insurance Categories</h2>
            <p className="text-xs text-slate-500 mt-0.5">Built on a modular architecture to support future expansions</p>
          </div>
          <Link to="/explore" className="text-xs font-semibold text-teal-700 hover:text-teal-800 flex items-center gap-1">
            View all categories <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link
            to="/explore?category=health"
            className="p-5 bg-white rounded-2xl border border-slate-200 hover:border-teal-600 hover:shadow-md transition-all group"
          >
            <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h4 className="font-bold text-slate-900 text-sm mb-1 group-hover:text-teal-800 transition-colors">Health Insurance</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Individual & Family floaters, critical illness, daycare procedures, and restore benefits.
            </p>
          </Link>

          <Link
            to="/explore?category=term-life"
            className="p-5 bg-white rounded-2xl border border-slate-200 hover:border-teal-600 hover:shadow-md transition-all group"
          >
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
              <Award className="w-5 h-5" />
            </div>
            <h4 className="font-bold text-slate-900 text-sm mb-1 group-hover:text-indigo-800 transition-colors">Term Life Insurance</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Pure risk protection up to ₹1-10 Crores for family financial security at low fixed rates.
            </p>
          </Link>

          <Link
            to="/explore?category=motor"
            className="p-5 bg-white rounded-2xl border border-slate-200 hover:border-teal-600 hover:shadow-md transition-all group"
          >
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
              <TrendingUp className="w-5 h-5" />
            </div>
            <h4 className="font-bold text-slate-900 text-sm mb-1 group-hover:text-amber-800 transition-colors">Motor Insurance</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Mandatory third-party liability and comprehensive own-damage with Zero Depreciation.
            </p>
          </Link>

          <Link
            to="/explore?category=travel"
            className="p-5 bg-white rounded-2xl border border-slate-200 hover:border-teal-600 hover:shadow-md transition-all group"
          >
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
              <Compass className="w-5 h-5" />
            </div>
            <h4 className="font-bold text-slate-900 text-sm mb-1 group-hover:text-emerald-800 transition-colors">Travel Insurance</h4>
            <p className="text-xs text-slate-500 leading-relaxed">
              Overseas medical emergencies, baggage loss, passport recovery, and trip cancellations.
            </p>
          </Link>
        </div>
      </section>
    </div>
  );
};
