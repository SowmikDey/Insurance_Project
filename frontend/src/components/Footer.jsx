import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldCheck, 
  ExternalLink, 
  AlertTriangle, 
  ArrowUp,
  Sparkles,
  BookOpen,
  HelpCircle,
  Compass,
  CheckCircle2,
  Database
} from 'lucide-react';

export const Footer = () => {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="bg-slate-950 text-slate-300 pt-14 pb-8 border-t border-slate-800 text-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Main Footer Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 lg:gap-6 mb-12">
          
          {/* 1. Brand & Mission */}
          <div className="lg:col-span-1 md:col-span-2 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-xs">
                <ShieldCheck className="w-5 h-5 text-teal-100" />
              </div>
              <div>
                <span className="font-extrabold text-white text-lg tracking-tight">
                  Bima<span className="text-teal-400">Gyan</span>
                </span>
                <span className="ml-2 text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800/80">
                  India
                </span>
              </div>
            </div>

            <p className="text-slate-400 leading-relaxed text-xs">
              India's transparent insurance education and policy decision platform. Grounded in official IRDAI guidelines with zero commercial bias.
            </p>

            {/* Platform Trust Badges */}
            <div className="pt-2 space-y-2 text-[11px] text-slate-300">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                <span>100% Free & Zero Commission</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                <span>Never Sells or Solicits Insurance</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                <span>Audited Ingestion from IRDAI Sources</span>
              </div>
            </div>
          </div>

          {/* 2. Platform Navigation */}
          <div>
            <h4 className="font-semibold text-white uppercase tracking-wider text-[11px] mb-3.5 flex items-center gap-1.5">
              <span>Platform Hub</span>
            </h4>
            <ul className="space-y-2.5">
              <li>
                <Link to="/learn" className="text-slate-400 hover:text-white flex items-center gap-1.5 transition-colors">
                  <BookOpen className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                  <span>15 Learning Modules</span>
                </Link>
              </li>
              <li>
                <Link to="/explore" className="text-slate-400 hover:text-white flex items-center gap-1.5 transition-colors">
                  <Compass className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                  <span>Policy Explorer</span>
                </Link>
              </li>
              <li>
                <Link to="/assistant" className="text-slate-400 hover:text-white flex items-center gap-1.5 transition-colors">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span>Grounded AI Assistant</span>
                </Link>
              </li>
              <li>
                <Link to="/glossary" className="text-slate-400 hover:text-white flex items-center gap-1.5 transition-colors">
                  <HelpCircle className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                  <span>30+ Insurance Glossary</span>
                </Link>
              </li>
              <li>
                <Link to="/admin" className="text-slate-400 hover:text-white flex items-center gap-1.5 transition-colors">
                  <Database className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                  <span>Ingested Documents & Audit</span>
                </Link>
              </li>
            </ul>
          </div>

          {/* 3. Popular Learning Modules */}
          <div>
            <h4 className="font-semibold text-white uppercase tracking-wider text-[11px] mb-3.5">
              Essential Modules
            </h4>
            <ul className="space-y-2 text-slate-400">
              <li>
                <Link to="/learn/what-is-insurance" className="hover:text-teal-400 transition-colors block truncate" title="Risk Pooling & Insurance Basics">
                  Risk Pooling Basics
                </Link>
              </li>
              <li>
                <Link to="/learn/understanding-health-insurance" className="hover:text-teal-400 transition-colors block truncate" title="Cashless vs Reimbursement">
                  Cashless vs. Reimbursement
                </Link>
              </li>
              <li>
                <Link to="/learn/deductibles-copayments-sublimits" className="hover:text-teal-400 transition-colors block truncate" title="Room Rent & Deductibles">
                  Room Rent & Co-Pay Traps
                </Link>
              </li>
              <li>
                <Link to="/learn/waiting-periods-ped-exclusions" className="hover:text-teal-400 transition-colors block truncate" title="Waiting Periods & Pre-Existing Diseases">
                  Waiting Periods & PED
                </Link>
              </li>
              <li>
                <Link to="/learn/term-life-vs-investment-schemes" className="hover:text-teal-400 transition-colors block truncate" title="Term Life vs Endowment">
                  Term Life vs. Endowment/ULIPs
                </Link>
              </li>
              <li>
                <Link to="/learn/super-top-up-explained" className="hover:text-teal-400 transition-colors block truncate" title="Super Top-Up Hack">
                  Super Top-Up Hack (₹25L Cover)
                </Link>
              </li>
              <li>
                <Link to="/learn/claim-filing-and-rejection" className="hover:text-teal-400 transition-colors block truncate" title="Claim Rejections & Grievance Filing">
                  Rejection Reasons & Appeals
                </Link>
              </li>
            </ul>
          </div>

          {/* 4. Essential Insurance Terms */}
          <div>
            <h4 className="font-semibold text-white uppercase tracking-wider text-[11px] mb-3.5">
              Glossary Terms
            </h4>
            <ul className="space-y-2 text-slate-400">
              <li>
                <Link to="/glossary/deductible" className="hover:text-teal-400 transition-colors block truncate">
                  Deductible vs. Co-Payment
                </Link>
              </li>
              <li>
                <Link to="/glossary/pre-existing-diseases" className="hover:text-teal-400 transition-colors block truncate">
                  Pre-Existing Diseases (PED)
                </Link>
              </li>
              <li>
                <Link to="/glossary/room-rent-capping" className="hover:text-teal-400 transition-colors block truncate">
                  Room Rent Capping
                </Link>
              </li>
              <li>
                <Link to="/glossary/restoration-benefit" className="hover:text-teal-400 transition-colors block truncate">
                  Restoration / Refill Cover
                </Link>
              </li>
              <li>
                <Link to="/glossary/no-claim-bonus" className="hover:text-teal-400 transition-colors block truncate">
                  No Claim Bonus (NCB)
                </Link>
              </li>
              <li>
                <Link to="/glossary/claim-settlement-ratio" className="hover:text-teal-400 transition-colors block truncate">
                  Claim Settlement Ratio (CSR)
                </Link>
              </li>
              <li>
                <Link to="/glossary/zero-depreciation" className="hover:text-teal-400 transition-colors block truncate">
                  Zero Depreciation (Bumper to Bumper)
                </Link>
              </li>
            </ul>
          </div>

          {/* 5. Official Indian Regulatory Authorities */}
          <div>
            <h4 className="font-semibold text-white uppercase tracking-wider text-[11px] mb-3.5">
              Official Authorities
            </h4>
            <ul className="space-y-2.5">
              <li>
                <a
                  href="https://www.irdai.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-400 hover:text-teal-400 flex items-center justify-between gap-1 group transition-colors"
                >
                  <span className="truncate">IRDAI Official Portal</span>
                  <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-teal-400 shrink-0" />
                </a>
              </li>
              <li>
                <a
                  href="https://policyholder.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-400 hover:text-teal-400 flex items-center justify-between gap-1 group transition-colors"
                >
                  <span className="truncate">IRDAI Policyholder Portal</span>
                  <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-teal-400 shrink-0" />
                </a>
              </li>
              <li>
                <a
                  href="https://bimabharosa.irdai.gov.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-400 hover:text-teal-400 flex items-center justify-between gap-1 group transition-colors"
                >
                  <span className="truncate">Bima Bharosa (Grievances)</span>
                  <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-teal-400 shrink-0" />
                </a>
              </li>
              <li>
                <a
                  href="https://www.cioins.co.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-400 hover:text-teal-400 flex items-center justify-between gap-1 group transition-colors"
                >
                  <span className="truncate">Council of Insurance Ombudsmen</span>
                  <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-teal-400 shrink-0" />
                </a>
              </li>
              <li>
                <a
                  href="https://www.gicouncil.in"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-400 hover:text-teal-400 flex items-center justify-between gap-1 group transition-colors"
                >
                  <span className="truncate">General Insurance Council</span>
                  <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-teal-400 shrink-0" />
                </a>
              </li>
              <li>
                <a
                  href="https://www.lifeinscouncil.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-slate-400 hover:text-teal-400 flex items-center justify-between gap-1 group transition-colors"
                >
                  <span className="truncate">Life Insurance Council</span>
                  <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-teal-400 shrink-0" />
                </a>
              </li>
            </ul>
          </div>

        </div>

        {/* Regulatory & Advisory Disclaimer Banner */}
        <div className="bg-slate-900/90 rounded-2xl p-5 border border-slate-800 mb-8 shadow-xs">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-slate-300 font-semibold text-xs">
                Statutory Consumer Notice & Educational Disclaimer
              </p>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                BimaGyan is an independent, non-commercial public education and consumer decision-support project. We are not an insurance company, agent, broker, corporate agent, or web aggregator registered under IRDAI regulations. We do not sell insurance, solicit policies, collect premiums, or accept commissions from any insurance provider. All policy summaries, indicative premiums, and comparison metrics are derived from public rate cards and official IRDAI-registered documents. Premium rates vary based on age, gender, medical underwriting, pin-code, and applicable GST. Consumers are strictly advised to review the official policy prospectus, terms and conditions, and Sales Illustrations filed with IRDAI before purchasing any insurance product.
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Colophon Bar */}
        <div className="border-t border-slate-800/80 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-slate-500 text-[11px]">
          <div className="flex items-center gap-2">
            <span>© {new Date().getFullYear()} BimaGyan Platform. Built for Indian First-Time Buyers.</span>
          </div>

          <div className="flex items-center gap-6">
            <span className="text-slate-400 font-medium">Free, Transparent & Open Access</span>
            <button
              onClick={scrollToTop}
              className="flex items-center gap-1.5 text-slate-400 hover:text-teal-400 transition-colors cursor-pointer"
              title="Scroll to top of page"
            >
              <span>Back to top</span>
              <ArrowUp className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

      </div>
    </footer>
  );
};
