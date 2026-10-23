import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Hospital, Building2 } from 'lucide-react';
import { HighlightedText } from './HighlightedText';

export const PolicyCard = ({ policy }) => {
  const minLakhs = (policy.min_sum_insured || 0) / 100000;
  const maxLakhs = (policy.max_sum_insured || 0) / 100000;
  const coverageStr = maxLakhs >= 100 
    ? `₹${minLakhs}L - ₹${(maxLakhs / 100).toFixed(1)} Cr`
    : `₹${minLakhs}L - ₹${maxLakhs}L`;

  const premiumStr = policy.indicative_annual_premium 
    ? `₹${policy.indicative_annual_premium.toLocaleString('en-IN')}`
    : 'Custom quote';

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between overflow-hidden group">
      {/* Top Banner / Category */}
      <div className="p-5 pb-0">
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="text-[11px] font-semibold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700">
            {policy.category?.name || 'Insurance'}
          </span>
          <span className="text-[10px] text-slate-500 font-mono">
            {policy.uin_number || 'IRDAI Registered'}
          </span>
        </div>

        {/* Insurer & Title */}
        <div className="mb-3">
          <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
            <Building2 className="w-3.5 h-3.5 text-slate-400" />
            <span>{policy.insurer?.name}</span>
            {policy.insurer?.claim_settlement_ratio && (
              <span className="ml-auto font-medium text-emerald-800 bg-emerald-50 px-2 py-0.2 rounded text-[11px] border border-emerald-200/60">
                CSR: {policy.insurer.claim_settlement_ratio}%
              </span>
            )}
          </div>
          <h3 className="text-base font-bold text-slate-900 group-hover:text-teal-800 transition-colors">
            <Link to={`/policies/${policy.slug}`}>
              {policy.name}
            </Link>
          </h3>
        </div>

        {/* Financial Highlights Pill Box */}
        <div className="grid grid-cols-2 gap-2 p-3 bg-slate-50/80 rounded-xl border border-slate-100 mb-4">
          <div>
            <span className="text-[10px] text-slate-500 block uppercase font-medium">Coverage Sum</span>
            <span className="text-xs font-bold text-slate-900">{coverageStr}</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-500 block uppercase font-medium">Indicative Premium</span>
            <div className="flex items-baseline gap-1">
              <span className="text-xs font-extrabold text-teal-800">{premiumStr}</span>
              <span className="text-[10px] text-slate-400">/year</span>
            </div>
          </div>
        </div>

        {/* Key Features with Contextual Varsity Highlights */}
        <div className="space-y-2 text-xs text-slate-600 mb-4">
          {policy.room_rent_capping && (
            <div className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-600 mt-1.5 shrink-0" />
              <div>
                <span className="text-slate-500">Room Rent: </span>
                <HighlightedText text={policy.room_rent_capping} className="font-medium text-slate-800" />
              </div>
            </div>
          )}

          {policy.copay_description && (
            <div className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-600 mt-1.5 shrink-0" />
              <div>
                <span className="text-slate-500">Co-pay: </span>
                <HighlightedText text={`${policy.copay_percentage || 0}% (${policy.copay_description})`} className="font-medium text-slate-800" />
              </div>
            </div>
          )}

          {policy.restoration_benefit && (
            <div className="flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-600 mt-1.5 shrink-0" />
              <div>
                <span className="text-slate-500">Restoration: </span>
                <HighlightedText text={policy.restoration_benefit} className="font-medium text-slate-800" />
              </div>
            </div>
          )}

          {policy.cashless_network_size > 0 && (
            <div className="flex items-center gap-1.5 text-[11px] text-slate-500 pt-1">
              <Hospital className="w-3.5 h-3.5 text-slate-400" />
              <span>{policy.cashless_network_size.toLocaleString('en-IN')}+ Cashless Hospitals</span>
            </div>
          )}
        </div>
      </div>

      {/* Card Action Footer */}
      <div className="px-5 py-3.5 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
        <span className="text-[10px] text-slate-400">
          Last verified: {policy.last_verified_date || 'Current FY'}
        </span>
        <Link
          to={`/policies/${policy.slug}`}
          className="text-xs font-semibold text-teal-800 hover:text-teal-900 flex items-center gap-1 transition-colors"
        >
          View Full Policy <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
