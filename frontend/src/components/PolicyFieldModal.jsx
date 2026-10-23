/**
 * PolicyFieldModal.jsx
 *
 * An accessible, contextual explanation modal for insurance policy attributes.
 * Explains each field in plain language with a definition, practical example,
 * trade-off analysis, the actual policy value, and the source evidence citation.
 *
 * Usage:
 *   <PolicyFieldModal
 *     fieldKey="copay_percentage"
 *     fieldValue="20%"
 *     evidence={{ snippet: "...", page: 12, section: "Co-payment", source_url: "..." }}
 *     onClose={() => setActiveModal(null)}
 *   />
 */
import React, { useEffect, useRef } from 'react';
import { X, Info, BookOpen, Lightbulb, AlertTriangle, FileText } from 'lucide-react';

// ─── Centralised field-explanation registry ───────────────────────────────────
// Each entry has: label, definition, why_it_matters, how_to_interpret, example,
//                caveats, preference (lower_is_better | higher_is_better | context_dependent)
const FIELD_EXPLANATIONS = {
  sum_insured: {
    label: 'Sum Insured',
    definition:
      'The maximum amount your insurance company will pay towards covered medical expenses during a policy year.',
    why_it_matters:
      'If your total eligible hospital bills exceed this limit in a year, you bear the balance out of pocket. Choosing an adequate sum insured is the single most important decision in a health policy.',
    how_to_interpret:
      'Higher sum insured means more financial protection, but a higher sum insured does not make a policy better in every other respect — room-rent limits, co-payments and exclusions must also be considered.',
    example:
      'Example: If your sum insured is ₹5 lakh and your hospital bill is ₹6 lakh, the insurer pays up to ₹5 lakh (subject to other terms). The remaining ₹1 lakh is your liability.',
    caveats:
      'A ₹1 crore sum insured with a strict 1% room-rent sub-limit may cover less of your actual bill than a ₹25 lakh policy with no room-rent limit, depending on the hospital category.',
    preference: 'higher_is_better',
  },
  room_rent_capping: {
    label: 'Room Rent Capping / Limit',
    definition:
      'A cap on the maximum daily room-rent your policy will pay for. If you choose a room that exceeds this limit, you may face proportionate deductions on ALL associated charges — not just the room rent.',
    why_it_matters:
      'Room-rent limits have a hidden multiplier effect. Insurers use the room category to proportionally reduce surgeon fees, ICU charges, anaesthesia and other costs if you stay in a room above your entitled category.',
    how_to_interpret:
      'Fewer or no room-rent restrictions is generally preferable because it reduces the risk of proportionate deductions. A "Single Private AC Room" entitlement is generally better than a "1% of sum insured per day" cap at lower sum-insured levels.',
    example:
      'Example: Sum insured ₹5L with a 1% cap = ₹5,000/day room limit. A ₹8,000/day room triggers a 60% proportionate payout on ALL charges (₹5k/₹8k). A ₹1L surgery claim may yield only ₹60,000.',
    caveats:
      'Even "single private room" entitlement can be restricted if the hospital classifies rooms differently. Always verify the hospital\'s room categorisation.',
    preference: 'context_dependent',
  },
  copay_percentage: {
    label: 'Co-payment (Co-pay)',
    definition:
      'The fixed percentage of every eligible claim that you, the policyholder, must pay from your own pocket. The insurer covers the remaining percentage.',
    why_it_matters:
      'Co-payment directly reduces what the insurer pays. A higher co-pay means a bigger out-of-pocket expense every time you make a claim.',
    how_to_interpret:
      'A lower co-payment is generally better for the insured, all else equal, because you pay a smaller share of eligible expenses. A 0% co-pay is ideal.',
    example:
      'Example: Hospital bill = ₹2,00,000. With a 20% co-pay, you pay ₹40,000 and the insurer pays ₹1,60,000. With 0% co-pay, the insurer pays the full ₹2,00,000 (subject to sum insured).',
    caveats:
      'Some policies impose co-pay only for specific conditions (senior citizens, pre-existing diseases, or certain hospital types). Read the exact co-pay clause carefully.',
    preference: 'lower_is_better',
  },
  icu_sub_limit: {
    label: 'ICU Sub-limit',
    definition:
      'A separate cap on what the insurer pays specifically for Intensive Care Unit (ICU) charges, often set as a percentage of the sum insured per day.',
    why_it_matters:
      "ICU stays are extremely expensive. A strict ICU sub-limit can mean a very large unpaid balance even after the insurer's contribution.",
    how_to_interpret:
      'No ICU sub-limit (or "actuals up to sum insured") is generally preferable. A "2% of sum insured per day" ICU cap may be insufficient for high-end hospitals.',
    example:
      'Example: Sum insured ₹5L. ICU cap = 2% = ₹10,000/day. Actual ICU charge = ₹30,000/day. You pay ₹20,000/day out of pocket, irrespective of your overall sum insured.',
    caveats:
      'The room-rent proportionate-deduction rule may apply additionally on top of the ICU sub-limit.',
    preference: 'context_dependent',
  },
  initial_waiting_period: {
    label: 'Initial Waiting Period',
    definition:
      'The period at the start of your policy during which most illnesses (excluding accidents) are NOT covered.',
    why_it_matters:
      'If you need hospitalisation for a non-accidental illness within this period, your claim will be rejected. Only accidental emergencies are typically covered during this window.',
    how_to_interpret:
      'A shorter initial waiting period is generally more favourable. The standard is 30 days; some policies offer shorter periods.',
    example:
      'Example: A 30-day initial waiting period means a policy starting on 1 Jan will cover non-accidental illnesses only from 31 Jan onwards.',
    caveats:
      'Accidental injuries (fractures, burns, etc.) are typically covered from Day 1. Verify the exact definition of "accident" in the policy wording.',
    preference: 'lower_is_better',
  },
  ped_waiting_period: {
    label: 'Pre-existing Disease (PED) Waiting Period',
    definition:
      'The period you must wait before your insurance covers treatment for any disease, condition, or ailment you had before buying the policy — including conditions you were diagnosed with or received treatment for.',
    why_it_matters:
      'This is the most consequential waiting period for most buyers. If you have diabetes, hypertension, thyroid disorders, or any previous illness, related claims will be rejected until this period expires.',
    how_to_interpret:
      'A shorter PED waiting period is generally more favourable. The standard is 36 months; some policies offer 24 months. IRDAI mandates a maximum of 48 months.',
    example:
      'Example: You have Type 2 Diabetes. Your policy has a 36-month PED waiting period. Any diabetes-related hospitalisation in the first 3 years is rejected. Treatment from Year 4 onwards is covered.',
    caveats:
      'Non-disclosure of a pre-existing condition is the most common reason for claim rejection. Always declare all past and current conditions truthfully.',
    preference: 'lower_is_better',
  },
  specific_illness_waiting_period: {
    label: 'Specific Illness Waiting Period',
    definition:
      'A waiting period applied to specific named medical conditions listed in the policy, regardless of whether you had them before buying the policy.',
    why_it_matters:
      'Common conditions like cataracts, hernia, knee replacements, gallstones, and back surgeries are frequently subject to a 24-month waiting period even if they were not pre-existing.',
    how_to_interpret:
      'A shorter or absent specific illness waiting period is preferable. Compare the list of named illnesses across policies carefully.',
    example:
      'Example: Your policy has a 24-month specific illness waiting period for cataracts. Even if your eyes were healthy when you bought the policy, a cataract claim in Month 18 will be rejected.',
    caveats:
      'The list of "specific named illnesses" varies by insurer and policy. Always check the schedule of waiting periods in the policy document.',
    preference: 'lower_is_better',
  },
  restoration_benefit: {
    label: 'Restoration Benefit (Sum Insured Recharge)',
    definition:
      'A feature that automatically reinstates (restores) your sum insured after it is exhausted due to a claim during the policy year.',
    why_it_matters:
      'Without restoration, once your sum insured is exhausted you have no cover for the rest of the year. Restoration effectively gives you a second layer of protection.',
    how_to_interpret:
      'Restoration is generally a positive feature, but the terms determine its true value: when does it trigger, what can it be used for, and how many times in a year?',
    example:
      'Example: ₹5L sum insured with 100% restoration. First claim = ₹5L (exhausted). Restoration adds back ₹5L. Second hospitalisation = ₹3L (covered). Without restoration, the second claim is entirely out of pocket.',
    caveats:
      'Many policies restrict restored sum insured to a different illness or family member. Some require complete exhaustion before restoration triggers. Some offer restoration only once per year.',
    preference: 'context_dependent',
  },
  no_claim_bonus: {
    label: 'No Claim Bonus (NCB)',
    definition:
      'An increase in your sum insured granted for every claim-free policy year, at no additional premium cost.',
    why_it_matters:
      'NCB effectively grows your coverage over time if you stay healthy, which is an important long-term benefit given healthcare cost inflation.',
    how_to_interpret:
      'A higher NCB percentage per year and a higher cumulative NCB cap are generally better. However, NCB may be reduced or reset after a claim in many policies.',
    example:
      'Example: ₹5L base sum insured, 50% NCB per claim-free year up to 100% maximum. After 2 claim-free years: ₹7.5L effective cover. After 2 more claim-free years: ₹10L (capped at 100% bonus).',
    caveats:
      'NCB may be partially or fully reset upon a claim. Some policies retain NCB at a reduced rate even after a claim — check the exact clause.',
    preference: 'higher_is_better',
  },
  ambulance_cover: {
    label: 'Ambulance Cover',
    definition:
      'Coverage for road ambulance charges incurred to transport the patient to and sometimes from the hospital.',
    why_it_matters:
      'Emergency ambulance costs can range from ₹2,000 to ₹20,000+ in metro cities. Some critical care ambulances (equipped with ventilators) can cost ₹50,000 or more per trip.',
    how_to_interpret:
      'Actuals or "up to sum insured" is the most comprehensive cover. Sub-limits of ₹2,000–5,000 may be inadequate in major cities.',
    example:
      'Example: ₹5,000 ambulance sub-limit. Actual cost: ₹15,000. You pay ₹10,000 out of pocket. With "actuals covered" there is no out-of-pocket expense.',
    caveats:
      'Air ambulance cover, if required, is a separate and much more expensive benefit usually not included by default.',
    preference: 'context_dependent',
  },
  pre_hospitalization_days: {
    label: 'Pre-hospitalisation Cover',
    definition:
      'The number of days before the date of hospital admission for which the insurer will cover related medical expenses (consultations, diagnostic tests, medicines prescribed for the same illness).',
    why_it_matters:
      'Diagnostic workups before planned hospitalisation can be expensive. A longer pre-hospitalisation window reduces your out-of-pocket spend.',
    how_to_interpret:
      'A longer pre-hospitalisation cover window is generally better. The standard varies from 30 to 60 days.',
    example:
      'Example: 30-day pre-hospitalisation cover. If you were hospitalised on 1 April, bills from 1 March onwards for the same illness are covered.',
    caveats:
      'Only expenses directly related to the condition leading to hospitalisation are covered. Routine check-ups or unrelated consultations are excluded.',
    preference: 'higher_is_better',
  },
  post_hospitalization_days: {
    label: 'Post-hospitalisation Cover',
    definition:
      'The number of days after discharge from hospital for which the insurer will cover follow-up expenses — consultations, medicines, physiotherapy — for the same illness.',
    why_it_matters:
      'Recovery costs after a major surgery or illness can be substantial. Medicines, physiotherapy, and follow-up consultations add up quickly.',
    how_to_interpret:
      'A longer post-hospitalisation window is generally better. Standard policies offer 60–90 days; some offer up to 180 days.',
    example:
      'Example: 90-day post-hospitalisation cover. If discharged on 1 April, follow-up physiotherapy and medicines for the same condition are covered until 30 June.',
    caveats:
      'Post-hospitalisation cover is limited to expenses for the same illness that caused hospitalisation. Ongoing chronic disease management is excluded unless hospitalised again.',
    preference: 'higher_is_better',
  },
  deductible: {
    label: 'Deductible',
    definition:
      'The fixed amount you must pay out of pocket for each claim before the insurer starts paying. Unlike co-payment (a percentage), a deductible is a fixed rupee amount.',
    why_it_matters:
      'A high deductible significantly reduces the effective value of your cover for smaller claims. It is primarily used in super top-up plans to reduce premium.',
    how_to_interpret:
      'A lower deductible is generally better for standalone health policies. Super top-up plans intentionally have a high deductible, intended to sit on top of a base policy.',
    example:
      'Example: ₹2L deductible. Hospital bill = ₹3.5L. You pay ₹2L; insurer pays ₹1.5L. If the bill is ₹1.8L (below the deductible), the insurer pays nothing.',
    caveats:
      'In super top-up plans the deductible is the threshold above which the plan kicks in. The deductible is typically borne by your base policy, not paid out of pocket.',
    preference: 'lower_is_better',
  },
};

// Preference badge component
const PreferenceBadge = ({ preference }) => {
  if (preference === 'lower_is_better') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
        ↓ Lower is generally better
      </span>
    );
  }
  if (preference === 'higher_is_better') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-800 border border-blue-200">
        ↑ Higher is generally better
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200">
      ⚖ Context-dependent
    </span>
  );
};

// ─── Main Modal Component ─────────────────────────────────────────────────────
export const PolicyFieldModal = ({ fieldKey, fieldValue, evidence, onClose }) => {
  const overlayRef = useRef(null);
  const closeButtonRef = useRef(null);

  const info = FIELD_EXPLANATIONS[fieldKey];

  // Focus trap and keyboard accessibility
  useEffect(() => {
    closeButtonRef.current?.focus();
    const handleKey = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  const handleOverlayClick = (e) => {
    if (e.target === overlayRef.current) onClose();
  };

  if (!info) {
    // No explanation registered — show a minimal modal
    return (
      <div
        ref={overlayRef}
        onClick={handleOverlayClick}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        role="dialog"
        aria-modal="true"
        aria-label="Field explanation"
      >
        <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-4">
          <div className="flex items-start justify-between">
            <h2 className="text-base font-bold text-slate-900 capitalize">
              {fieldKey.replace(/_/g, ' ')}
            </h2>
            <button
              ref={closeButtonRef}
              onClick={onClose}
              className="text-slate-400 hover:text-slate-700 transition-colors cursor-pointer"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          {fieldValue && (
            <div className="p-3 bg-teal-50 rounded-xl border border-teal-200 text-sm font-bold text-teal-800">
              Policy value: {fieldValue}
            </div>
          )}
          <p className="text-xs text-slate-500">
            No detailed explanation is available for this field yet.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="field-modal-title"
    >
      <div className="bg-white rounded-2xl shadow-2xl max-w-xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between p-5 pb-4 border-b border-slate-100 shrink-0">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-teal-700" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-teal-700">
                Policy Term Explained
              </span>
            </div>
            <h2
              id="field-modal-title"
              className="text-xl font-extrabold text-slate-900"
            >
              {info.label}
            </h2>
            <PreferenceBadge preference={info.preference} />
          </div>
          <button
            ref={closeButtonRef}
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 transition-colors cursor-pointer shrink-0 mt-1"
            aria-label="Close explanation modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable body */}
        <div className="overflow-y-auto flex-1 p-5 space-y-5 text-sm">
          {/* 1. What it means */}
          <section className="space-y-1.5">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wide flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-teal-600" />
              What it means
            </h3>
            <p className="text-slate-700 leading-relaxed">{info.definition}</p>
          </section>

          {/* 2. Why it matters */}
          <section className="space-y-1.5">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wide flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
              Why it matters
            </h3>
            <p className="text-slate-700 leading-relaxed">{info.why_it_matters}</p>
          </section>

          {/* 3. Practical example */}
          <section className="p-3.5 bg-blue-50/70 border border-blue-200/70 rounded-xl space-y-1.5">
            <h3 className="text-xs font-bold text-blue-800 uppercase tracking-wide flex items-center gap-1.5">
              <Lightbulb className="w-3.5 h-3.5 text-blue-600" />
              Practical Example
            </h3>
            <p className="text-blue-950 leading-relaxed text-xs">{info.example}</p>
          </section>

          {/* 4. How to interpret */}
          <section className="space-y-1.5">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wide">
              How to interpret this value
            </h3>
            <p className="text-slate-700 leading-relaxed">{info.how_to_interpret}</p>
          </section>

          {/* 5. Caveats */}
          <section className="p-3.5 bg-amber-50/70 border border-amber-200/70 rounded-xl space-y-1.5">
            <h3 className="text-xs font-bold text-amber-800 uppercase tracking-wide">
              ⚠ Trade-offs & Caveats
            </h3>
            <p className="text-amber-950 leading-relaxed text-xs">{info.caveats}</p>
          </section>

          {/* 6. Actual policy value */}
          {fieldValue && (
            <section className="p-3.5 bg-teal-50/80 border border-teal-200 rounded-xl space-y-1">
              <h3 className="text-xs font-bold text-teal-800 uppercase tracking-wide">
                This Policy's Value
              </h3>
              <span className="text-lg font-extrabold text-teal-900">{fieldValue}</span>
            </section>
          )}

          {/* 7. Evidence */}
          {evidence && (evidence.snippet || evidence.source_url) && (
            <section className="space-y-1.5">
              <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wide flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-slate-500" />
                Source Evidence
              </h3>
              {evidence.snippet && (
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 italic leading-relaxed">
                  "{evidence.snippet}"
                </div>
              )}
              <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 pt-1">
                {evidence.page && (
                  <span className="text-slate-600 font-medium">Page {evidence.page}</span>
                )}
                {evidence.section && (
                  <span>Section: <strong className="text-slate-600">{evidence.section}</strong></span>
                )}
                {evidence.source_url && (
                  <a
                    href={evidence.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-teal-700 underline hover:text-teal-900"
                  >
                    View Source Document
                  </a>
                )}
              </div>
            </section>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100 shrink-0 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-teal-800 text-white rounded-xl text-xs font-semibold hover:bg-teal-900 transition-colors cursor-pointer"
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};

// Export the field keys registry for use in PolicyDetailsPage
export { FIELD_EXPLANATIONS };
