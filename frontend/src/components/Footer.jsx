import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, ExternalLink, Heart, AlertTriangle } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="bg-slate-900 text-slate-300 pt-12 pb-8 border-t border-slate-800 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          {/* Brand & Mission */}
          <div className="md:col-span-1 space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-teal-100" />
              </div>
              <span className="font-bold text-white text-lg tracking-tight">
                Bima<span className="text-teal-400">Gyan</span>
              </span>
            </div>
            <p className="text-slate-400 leading-relaxed text-xs">
              Empowering people in India with free, transparent insurance education, policy exploration, and grounded AI guidance.
            </p>
            <div className="pt-1 flex items-center gap-1.5 text-[11px] text-teal-400 font-medium">
              <span>🇮🇳 Built specifically for Indian consumers</span>
            </div>
          </div>

          {/* Quick Platform Links */}
          <div>
            <h4 className="font-semibold text-white uppercase tracking-wider text-[11px] mb-3">
              Platform Sections
            </h4>
            <ul className="space-y-2">
              <li>
                <Link to="/learn" className="text-slate-400 hover:text-white transition-colors">
                  10 Free Learning Modules
                </Link>
              </li>
              <li>
                <Link to="/explore" className="text-slate-400 hover:text-white transition-colors">
                  Insurance Policy Explorer
                </Link>
              </li>
              <li>
                <Link to="/assistant" className="text-slate-400 hover:text-white transition-colors">
                  AI Insurance Assistant (RAG)
                </Link>
              </li>
              <li>
                <Link to="/glossary" className="text-slate-400 hover:text-white transition-colors">
                  Varsity Insurance Glossary
                </Link>
              </li>
              <li>
                <Link to="/admin" className="text-slate-400 hover:text-white transition-colors">
                  Data Ingestion & Ingested Sources
                </Link>
              </li>
            </ul>
          </div>

          {/* Key Insurance Concepts */}
          <div>
            <h4 className="font-semibold text-white uppercase tracking-wider text-[11px] mb-3">
              Essential Concepts
            </h4>
            <ul className="space-y-2 text-slate-400">
              <li>
                <Link to="/glossary/deductible" className="hover:text-white transition-colors">
                  What is a Deductible?
                </Link>
              </li>
              <li>
                <Link to="/glossary/copayment" className="hover:text-white transition-colors">
                  Co-payment Rules & Dangers
                </Link>
              </li>
              <li>
                <Link to="/glossary/room-rent-capping" className="hover:text-white transition-colors">
                  Room Rent Proportionate Deduction
                </Link>
              </li>
              <li>
                <Link to="/glossary/waiting-period" className="hover:text-white transition-colors">
                  3-Stage Waiting Periods in India
                </Link>
              </li>
              <li>
                <Link to="/glossary/claim-settlement-ratio" className="hover:text-white transition-colors">
                  Claim Settlement Ratio (CSR)
                </Link>
              </li>
              <li>
                <Link to="/glossary/zero-depreciation" className="hover:text-white transition-colors">
                  Zero Depreciation in Car Insurance
                </Link>
              </li>
            </ul>
          </div>

          {/* Official Indian Regulatory Portals */}
          <div>
            <h4 className="font-semibold text-white uppercase tracking-wider text-[11px] mb-3">
              Official Indian Authorities
            </h4>
            <ul className="space-y-2">
              <li>
                <a
                  href="https://policyholder.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-400 hover:text-teal-400 flex items-center gap-1 transition-colors"
                >
                  IRDAI Consumer Education <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>
                <a
                  href="https://bimabharosa.irdai.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-400 hover:text-teal-400 flex items-center gap-1 transition-colors"
                >
                  Bima Bharosa Grievance Portal <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>
                <a
                  href="https://www.cioins.co.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-400 hover:text-teal-400 flex items-center gap-1 transition-colors"
                >
                  Council of Insurance Ombudsmen <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>
                <a
                  href="https://www.gicouncil.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-400 hover:text-teal-400 flex items-center gap-1 transition-colors"
                >
                  General Insurance Council India <ExternalLink className="w-3 h-3" />
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Regulatory Disclaimer Banner */}
        <div className="bg-slate-800/80 rounded-xl p-4 border border-slate-700/60 mb-6 flex items-start gap-3">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p className="text-slate-400 text-[11px] leading-relaxed">
            <strong className="text-slate-200">Regulatory Disclaimer:</strong> BimaGyan is an independent, non-commercial educational and decision-support project. We do not sell insurance, solicit business, or act as an insurance intermediary, broker, or agent. Policy premiums displayed are indicative figures based on standard profiles and public rate cards; exact premiums vary according to individual age, location, medical underwriting, and tax rates. Always read the official prospectus and policy wordings registered with IRDAI before taking financial decisions.
          </p>
        </div>

        {/* Copyright */}
        <div className="border-t border-slate-800/80 pt-6 flex flex-col sm:flex-row items-center justify-between text-slate-500 text-[11px]">
          <p>© {new Date().getFullYear()} BimaGyan Platform. Built for Indian First-Time Buyers.</p>
          <p className="mt-2 sm:mt-0 flex items-center gap-1">
            Free & Open Education for All Indian Citizens
          </p>
        </div>
      </div>
    </footer>
  );
};
