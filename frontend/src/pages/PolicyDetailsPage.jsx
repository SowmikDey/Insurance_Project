import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { HighlightedText } from '../components/HighlightedText';
import { 
  Building2, 
  ShieldCheck, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  CheckCircle2,
  Info, 
  IndianRupee, 
  Hospital, 
  FileText, 
  ExternalLink, 
  ArrowLeft,
  Calendar,
  ThumbsUp,
  ThumbsDown,
  Quote,
  FileSearch,
  HelpCircle
} from 'lucide-react';
import { PolicyFieldModal } from '../components/PolicyFieldModal';

export const PolicyDetailsPage = () => {
  const { policySlug } = useParams();
  const navigate = useNavigate();

  const [policy, setPolicy] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // overview, benefits, exclusions, waiting, pricing, reviews, documents
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeModalField, setActiveModalField] = useState(null);

  useEffect(() => {
    const fetchPolicy = async () => {
      setLoading(true);
      try {
        const data = await api.getPolicyDetail(policySlug);
        setPolicy(data);
        window.scrollTo(0, 0);
      } catch (err) {
        setError(err.message || 'Policy not found');
      } finally {
        setLoading(false);
      }
    };
    fetchPolicy();
  }, [policySlug]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-24 px-4 text-center">
        <div className="w-10 h-10 border-3 border-teal-700 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-sm text-slate-500">Loading detailed policy wordings & IRDAI filings...</p>
      </div>
    );
  }

  if (error || !policy) {
    return (
      <div className="max-w-xl mx-auto py-20 px-4 text-center space-y-4">
        <AlertTriangle className="w-10 h-10 text-amber-500 mx-auto" />
        <h2 className="text-xl font-bold text-slate-900">Policy not found</h2>
        <p className="text-xs text-slate-500">The requested policy document or identifier does not exist in our database.</p>
        <button
          onClick={() => navigate('/explore')}
          className="px-4 py-2 bg-teal-800 text-white rounded-xl text-xs font-semibold cursor-pointer"
        >
          Return to Explorer
        </button>
      </div>
    );
  }

  let coverageStr = 'Coverage details upon proposal';
  if (policy.min_sum_insured && policy.max_sum_insured) {
    const minL = policy.min_sum_insured / 100000;
    const maxL = policy.max_sum_insured / 100000;
    coverageStr = maxL >= 100
      ? `₹${minL}L - ₹${(maxL / 100).toFixed(1)} Cr`
      : `₹${minL}L - ₹${maxL}L`;
  } else if (policy.max_sum_insured) {
    const maxL = policy.max_sum_insured / 100000;
    coverageStr = maxL >= 100 ? `Up to ₹${(maxL / 100).toFixed(1)} Cr` : `Up to ₹${maxL}L`;
  }

  const premiumStr = policy.indicative_annual_premium 
    ? `₹${policy.indicative_annual_premium.toLocaleString('en-IN')}`
    : 'Quote by Age';

  const openFieldModal = (fieldKey, displayValue) => {
    // Look up matching fact in policy.facts for exact evidence citation
    const matchingFact = policy.facts?.find(
      (f) => f.field_name?.toLowerCase() === fieldKey.toLowerCase()
    );
    setActiveModalField({
      fieldKey,
      fieldValue: displayValue || (policy[fieldKey] !== undefined && policy[fieldKey] !== null ? String(policy[fieldKey]) : 'Not specified in policy wording'),
      evidence: matchingFact
        ? {
            snippet: matchingFact.evidence_snippet,
            page: matchingFact.page_number,
            section: matchingFact.section_heading,
            source_url: matchingFact.source_url || policy.policy_wording_url,
          }
        : policy.policy_wording_url
        ? {
            source_url: policy.policy_wording_url,
          }
        : null,
    });
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back button */}
      <div>
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-teal-800 transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Browse</span>
        </button>
      </div>

      {/* Policy Hero Card */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/90 shadow-sm space-y-6">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 pb-6 border-b border-slate-100">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-teal-50 text-teal-800 border border-teal-200/60">
                {policy.category?.name || 'Insurance'}
              </span>
              <span className="text-xs text-slate-500 font-mono">
                UIN: {policy.uin_number || 'Registered with IRDAI'}
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {policy.name}
            </h1>

            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-600">
              <span className="flex items-center gap-1.5 font-medium">
                <Building2 className="w-4 h-4 text-slate-400" />
                {policy.insurer?.name}
              </span>
              {policy.insurer?.claim_settlement_ratio && (
                <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 font-bold border border-emerald-200">
                  CSR: {policy.insurer.claim_settlement_ratio}%
                </span>
              )}
              {policy.cashless_network_size > 0 && (
                <span className="flex items-center gap-1 text-slate-500">
                  <Hospital className="w-3.5 h-3.5 text-slate-400" />
                  {policy.cashless_network_size.toLocaleString('en-IN')}+ Cashless Hospitals
                </span>
              )}
            </div>
          </div>

          {/* Pricing & Compare CTA */}
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200/80 min-w-56 space-y-3">
            <div>
              <span className="text-[10px] text-slate-400 font-semibold uppercase block">
                Indicative Premium
              </span>
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-extrabold text-teal-800">{premiumStr}</span>
                <span className="text-xs text-slate-500">/year</span>
              </div>
              <span className="text-[10px] text-slate-400 block mt-0.5">Coverage: {coverageStr}</span>
            </div>

          </div>
        </div>

        {/* Indicative Quote Disclaimer Banner */}
        <div className="p-3 bg-amber-50/70 border border-amber-200/80 rounded-xl flex items-start gap-2.5 text-xs text-amber-950">
          <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
          <p className="leading-relaxed font-normal">
            <strong>Indicative Price Notice:</strong> {policy.premium_disclaimer || "Indicative premium for standard coverage. Actual quotes vary by age, city & health disclosures."}
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 overflow-x-auto border-b border-slate-200 pb-px scrollbar-none">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'benefits', label: `Benefits (${policy.benefits?.length || 0})` },
            { id: 'exclusions', label: `Exclusions (${policy.exclusions?.length || 0})` },
            { id: 'waiting', label: `Waiting Periods (${policy.waiting_periods?.length || 0})` },
            { id: 'facts', label: `Verifiable Evidence (${policy.facts?.length || 0})` },
            { id: 'documents', label: 'Verified Sources' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-all cursor-pointer ${
                activeTab === tab.id
                  ? 'border-teal-700 text-teal-800'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab 1: Overview */}
        {activeTab === 'overview' && (
          <div className="space-y-6 pt-2">
            <div className="space-y-2">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Policy Summary</h3>
              <p className="text-sm text-slate-700 leading-relaxed font-normal">
                <HighlightedText text={policy.summary} />
              </p>
            </div>

            {/* Quick Fact Grid with Interactive Educational Explanations */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500">Core Parameters</span>
                <span className="text-[11px] text-teal-700 font-medium flex items-center gap-1">
                  <HelpCircle className="w-3.5 h-3.5" /> Tap any parameter for plain-language explanation & trade-offs
                </span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                <div 
                  onClick={() => openFieldModal('room_rent_capping', policy.room_rent_capping)}
                  className="p-4 bg-slate-50 hover:bg-teal-50/60 rounded-xl border border-slate-200/80 hover:border-teal-300 transition-all cursor-pointer group"
                  title="Click to view definition, impact and calculations"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                    <span>Room Rent Capping</span>
                    <HelpCircle className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-700 transition-colors" />
                  </div>
                  <span className="text-xs font-bold text-slate-800 block mt-1 group-hover:text-teal-900">
                    <HighlightedText text={policy.room_rent_capping || 'Not specified'} />
                  </span>
                </div>

                <div 
                  onClick={() => openFieldModal('copay_percentage', policy.copay_percentage !== null ? `${policy.copay_percentage}% (${policy.copay_description || 'Standard'})` : null)}
                  className="p-4 bg-slate-50 hover:bg-teal-50/60 rounded-xl border border-slate-200/80 hover:border-teal-300 transition-all cursor-pointer group"
                  title="Click to view definition, impact and calculations"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                    <span>Co-payment</span>
                    <HelpCircle className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-700 transition-colors" />
                  </div>
                  <span className="text-xs font-bold text-slate-800 block mt-1 group-hover:text-teal-900">
                    <HighlightedText text={policy.copay_percentage !== null && policy.copay_percentage !== undefined ? `${policy.copay_percentage}% (${policy.copay_description || 'Co-pay clause'})` : 'No co-pay reported'} />
                  </span>
                </div>

                <div 
                  onClick={() => openFieldModal('restoration_benefit', policy.restoration_benefit)}
                  className="p-4 bg-slate-50 hover:bg-teal-50/60 rounded-xl border border-slate-200/80 hover:border-teal-300 transition-all cursor-pointer group"
                  title="Click to view definition, impact and calculations"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                    <span>Restoration Benefit</span>
                    <HelpCircle className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-700 transition-colors" />
                  </div>
                  <span className="text-xs font-bold text-slate-800 block mt-1 group-hover:text-teal-900">
                    <HighlightedText text={policy.restoration_benefit || 'Not specified'} />
                  </span>
                </div>

                <div 
                  onClick={() => openFieldModal('pre_hospitalization_days', `${policy.pre_hospitalization_days || 0} Days Pre / ${policy.post_hospitalization_days || 0} Days Post`)}
                  className="p-4 bg-slate-50 hover:bg-teal-50/60 rounded-xl border border-slate-200/80 hover:border-teal-300 transition-all cursor-pointer group"
                  title="Click to view definition, impact and calculations"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                    <span>Pre / Post Hospitalization</span>
                    <HelpCircle className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-700 transition-colors" />
                  </div>
                  <span className="text-xs font-bold text-slate-800 block mt-1 group-hover:text-teal-900">
                    {policy.pre_hospitalization_days || '-'} Days Pre / {policy.post_hospitalization_days || '-'} Days Post
                  </span>
                </div>

                <div 
                  onClick={() => openFieldModal('no_claim_bonus', policy.no_claim_bonus)}
                  className="p-4 bg-slate-50 hover:bg-teal-50/60 rounded-xl border border-slate-200/80 hover:border-teal-300 transition-all cursor-pointer group"
                  title="Click to view definition, impact and calculations"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                    <span>No Claim Bonus (NCB)</span>
                    <HelpCircle className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-700 transition-colors" />
                  </div>
                  <span className="text-xs font-bold text-slate-800 block mt-1 group-hover:text-teal-900">
                    <HighlightedText text={policy.no_claim_bonus || 'Standard cumulative bonus'} />
                  </span>
                </div>

                <div 
                  onClick={() => openFieldModal('sum_insured', coverageStr)}
                  className="p-4 bg-slate-50 hover:bg-teal-50/60 rounded-xl border border-slate-200/80 hover:border-teal-300 transition-all cursor-pointer group"
                  title="Click to view definition, impact and calculations"
                >
                  <div className="flex items-center justify-between text-[11px] text-slate-500 font-medium">
                    <span>Sum Insured Range</span>
                    <HelpCircle className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-700 transition-colors" />
                  </div>
                  <span className="text-xs font-bold text-slate-800 block mt-1 group-hover:text-teal-900">
                    {coverageStr}
                  </span>
                </div>
              </div>
            </div>

            {/* Pros and Cons */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-slate-100">
              <div className="bg-emerald-50/50 p-5 rounded-2xl border border-emerald-200/80 space-y-3">
                <div className="flex items-center gap-2 text-emerald-900 font-bold text-xs uppercase tracking-wider">
                  <ThumbsUp className="w-4 h-4 text-emerald-700" /> Key Strengths (Pros)
                </div>
                <ul className="space-y-2">
                  {policy.pros?.map((pro, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-emerald-950 leading-relaxed">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 mt-1.5 shrink-0" />
                      <span><HighlightedText text={pro} /></span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-rose-50/50 p-5 rounded-2xl border border-rose-200/80 space-y-3">
                <div className="flex items-center gap-2 text-rose-900 font-bold text-xs uppercase tracking-wider">
                  <ThumbsDown className="w-4 h-4 text-rose-700" /> Limitations & Caveats (Cons)
                </div>
                <ul className="space-y-2">
                  {policy.cons?.map((con, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-rose-950 leading-relaxed">
                      <span className="w-1.5 h-1.5 rounded-full bg-rose-600 mt-1.5 shrink-0" />
                      <span><HighlightedText text={con} /></span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Benefits */}
        {activeTab === 'benefits' && (
          <div className="space-y-4 pt-2">
            <div className="p-3 bg-teal-50/60 rounded-xl text-xs text-teal-900 border border-teal-200 flex items-center gap-2">
              <Info className="w-4 h-4 text-teal-700 shrink-0" />
              <span>Hover or tap any underlined insurance term for an interactive Zerodha Varsity-style explanation.</span>
            </div>

            <div className="space-y-3">
              {policy.benefits?.map((b) => (
                <div key={b.id} className="p-4 bg-slate-50/80 rounded-2xl border border-slate-200/80 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-slate-800">
                      <HighlightedText text={b.title} />
                    </h4>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600">
                      {b.sub_limit}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    <HighlightedText text={b.description} />
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: Exclusions */}
        {activeTab === 'exclusions' && (
          <div className="space-y-4 pt-2">
            <div className="p-3 bg-rose-50/60 rounded-xl text-xs text-rose-950 border border-rose-200 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-700 shrink-0 mt-0.5" />
              <span>These situations are explicitly NOT covered under the registered IRDAI policy wordings. Always review permanent exclusions before purchasing.</span>
            </div>

            <div className="space-y-3">
              {policy.exclusions?.map((ex) => (
                <div key={ex.id} className="p-4 bg-white rounded-2xl border border-slate-200 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-rose-900">
                      <HighlightedText text={ex.title} />
                    </h4>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-medium">
                      {ex.exclusion_type}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    <HighlightedText text={ex.description} />
                  </p>
                  {ex.irda_clause_ref && (
                    <span className="text-[10px] text-slate-400 block pt-1">
                      Clause Ref: {ex.irda_clause_ref}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 4: Waiting Periods */}
        {activeTab === 'waiting' && (
          <div className="space-y-4 pt-2">
            <div className="p-3 bg-teal-50/60 rounded-xl text-xs text-teal-900 border border-teal-200 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Info className="w-4 h-4 text-teal-700 shrink-0" />
                <span>IRDAI standard waiting periods define when claim eligibility begins.</span>
              </span>
              <span className="text-[11px] font-semibold text-teal-800">Tap any period for plain-language rules</span>
            </div>
            <div className="space-y-3">
              {policy.waiting_periods?.map((wp) => {
                const catLower = (wp.category || '').toLowerCase();
                const fieldKey = catLower.includes('initial')
                  ? 'initial_waiting_period'
                  : catLower.includes('pre-existing') || catLower.includes('ped')
                  ? 'ped_waiting_period'
                  : 'specific_illness_waiting_period';

                return (
                  <div
                    key={wp.id}
                    onClick={() => openFieldModal(fieldKey, `${wp.duration_months} Months — ${wp.category}`)}
                    className="p-4 bg-slate-50/90 hover:bg-teal-50/50 rounded-2xl border border-slate-200 hover:border-teal-300 transition-all cursor-pointer group space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-bold text-slate-900 group-hover:text-teal-950">
                          <HighlightedText text={wp.category} />
                        </h4>
                        <HelpCircle className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-700 transition-colors" />
                      </div>
                      <span className="text-xs font-extrabold text-teal-800 bg-teal-100/70 px-2.5 py-0.5 rounded-full">
                        {wp.duration_months} Months ({wp.duration_months < 12 ? `${wp.duration_months * 30} Days` : `${wp.duration_months / 12} Years`})
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      <HighlightedText text={wp.description} />
                    </p>
                    {wp.practical_impact && (
                      <div className="p-2.5 bg-amber-50 rounded-lg text-[11px] text-amber-950 border border-amber-200/70">
                        <strong>Real-world Impact:</strong> {wp.practical_impact}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Tab 5: Verifiable Facts & Evidence */}
        {activeTab === 'facts' && (
          <div className="space-y-4 pt-2 text-xs">
            <div className="p-3.5 bg-indigo-50/70 rounded-xl text-indigo-950 border border-indigo-200/80 flex items-start gap-2.5">
              <FileSearch className="w-4 h-4 text-indigo-700 shrink-0 mt-0.5" />
              <p className="leading-relaxed">
                <strong>Verifiable Evidence Citation:</strong> Every fact below is deterministically extracted from official registered policy wordings and customer information sheets with exact document quotes and page numbers.
              </p>
            </div>

            {!policy.facts || policy.facts.length === 0 ? (
              <div className="py-12 bg-slate-50 rounded-2xl border border-slate-200 text-center space-y-2">
                <FileText className="w-8 h-8 text-slate-400 mx-auto" />
                <h4 className="font-semibold text-slate-700">No structured facts extracted for this policy version yet</h4>
                <p className="text-slate-500 max-w-sm mx-auto">
                  Facts are extracted directly from official PDF wordings and verified by underwriters.
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {policy.facts.map((fact) => (
                  <div key={fact.id || fact.field_name} className="p-4 bg-white rounded-2xl border border-slate-200/90 shadow-2xs space-y-2.5">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 capitalize text-sm">
                          {fact.field_name.replace(/_/g, ' ')}
                        </span>
                        {fact.normalized_value && (
                          <span className="px-2 py-0.5 rounded-md bg-teal-50 text-teal-800 border border-teal-200 font-bold text-[11px]">
                            {fact.normalized_value}
                          </span>
                        )}
                      </div>
                      <div>
                        {fact.verification_status === 'VERIFIED' ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-bold">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Source Verified
                          </span>
                        ) : fact.verification_status === 'NEEDS_REVIEW' ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-bold">
                            <AlertTriangle className="w-3 h-3 text-amber-600" /> Needs Review
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200 text-[10px] font-bold">
                            <Clock className="w-3 h-3 text-slate-500" /> Extracted Fact
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Exact Evidence Snippet */}
                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-start gap-2.5 text-slate-700 italic">
                      <Quote className="w-4 h-4 text-slate-400 shrink-0 mt-0.5 not-italic" />
                      <div className="text-xs leading-relaxed not-italic text-slate-800">
                        "<HighlightedText text={fact.evidence_snippet} />"
                      </div>
                    </div>

                    {/* Document Provenance Details */}
                    <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 pt-1 border-t border-slate-100">
                      {fact.page_number && (
                        <span className="font-medium text-slate-600">
                          Page {fact.page_number}
                        </span>
                      )}
                      {fact.section_heading && (
                        <span>
                          Section: <strong className="text-slate-600 font-medium">{fact.section_heading}</strong>
                        </span>
                      )}
                      <span className="font-mono text-[10px]">
                        Method: {fact.extraction_method}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 6: Documents & Sources */}
        {activeTab === 'documents' && (
          <div className="space-y-4 pt-2 text-xs">
            <div className="space-y-3">
              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-800 block">Official Product Brochure & Prospectus</span>
                  <span className="text-[11px] text-slate-400">Registered marketing prospectus filed by {policy.insurer?.name}</span>
                </div>
                {policy.official_brochure_url ? (
                  <a
                    href={policy.official_brochure_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3.5 py-1.5 rounded-lg bg-teal-800 text-white font-medium hover:bg-teal-900 flex items-center gap-1 transition-colors"
                  >
                    View Brochure <ExternalLink className="w-3 h-3" />
                  </a>
                ) : (
                  <span className="text-slate-400">Available on insurer portal</span>
                )}
              </div>

              <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-800 block">Legally Binding Policy Wordings</span>
                  <span className="text-[11px] text-slate-400">Standard legal contract wording registered under IRDAI guidelines</span>
                </div>
                {policy.policy_wording_url ? (
                  <a
                    href={policy.policy_wording_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3.5 py-1.5 rounded-lg bg-slate-800 text-white font-medium hover:bg-slate-900 flex items-center gap-1 transition-colors"
                  >
                    Policy Wordings PDF <ExternalLink className="w-3 h-3" />
                  </a>
                ) : (
                  <span className="text-slate-400">Available in insurer library</span>
                )}
              </div>
            </div>

            <div className="p-3 bg-slate-100 rounded-xl text-[11px] text-slate-500 flex items-center justify-between">
              <span>Source Attribution: {policy.source_attribution}</span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" /> Last verified: {policy.last_verified_date || 'Current FY'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Accessible Interactive Detail Explanation Modal */}
      {activeModalField && (
        <PolicyFieldModal
          fieldKey={activeModalField.fieldKey}
          fieldValue={activeModalField.fieldValue}
          evidence={activeModalField.evidence}
          onClose={() => setActiveModalField(null)}
        />
      )}
    </div>
  );
};
