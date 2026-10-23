import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { PolicyCard } from '../components/PolicyCard';
import { 
  Search, 
  Filter, 
  SlidersHorizontal, 
  RotateCcw, 
  Info, 
  X,
  AlertCircle
} from 'lucide-react';

export const ExplorerPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [policies, setPolicies] = useState([]);
  const [categories, setCategories] = useState([]);
  const [insurers, setInsurers] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  // Filters state from URL or defaults
  const categoryFilter = searchParams.get('category') || 'all';
  const insurerFilter = searchParams.get('insurer') || 'all';
  const maxBudgetFilter = searchParams.get('max_budget') || '';
  const minSumInsuredFilter = searchParams.get('min_sum_insured') || '';
  const zeroCopayFilter = searchParams.get('zero_copay') === 'true';
  const noRoomRentFilter = searchParams.get('no_room_rent') === 'true';
  const searchQuery = searchParams.get('search') || '';
  const sortBy = searchParams.get('sort_by') || 'popular';

  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const [cats, ins] = await Promise.all([
          api.getCategories(),
          api.getInsurers()
        ]);
        setCategories(cats);
        setInsurers(ins);
      } catch (err) {
        console.error('Failed to load filter metadata:', err);
      }
    };
    fetchMetadata();
  }, []);

  useEffect(() => {
    const fetchFilteredPolicies = async () => {
      setLoading(true);
      try {
        const data = await api.getPolicies({
          category: categoryFilter,
          insurer: insurerFilter,
          max_budget: maxBudgetFilter ? parseFloat(maxBudgetFilter) : undefined,
          min_sum_insured: minSumInsuredFilter ? parseFloat(minSumInsuredFilter) : undefined,
          zero_copay: zeroCopayFilter,
          no_room_rent_capping: noRoomRentFilter,
          search: searchQuery,
          sort_by: sortBy,
          page: 1,
          page_size: 20
        });
        setPolicies(data.items || []);
        setTotal(data.total || 0);
      } catch (err) {
        console.error('Failed to query policies:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchFilteredPolicies();
  }, [categoryFilter, insurerFilter, maxBudgetFilter, minSumInsuredFilter, zeroCopayFilter, noRoomRentFilter, searchQuery, sortBy]);

  const updateFilter = (key, value) => {
    const next = new URLSearchParams(searchParams);
    if (value === null || value === '' || value === 'all' || value === false) {
      next.delete(key);
    } else {
      next.set(key, value.toString());
    }
    setSearchParams(next);
  };

  const handleResetFilters = () => {
    setSearchParams({});
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Insurance Policy Explorer
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Browse and filter verified policies across India with transparent, fine-print analysis.
          </p>
        </div>

        {/* Search bar */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search policy name, insurer..."
            value={searchQuery}
            onChange={(e) => updateFilter('search', e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-white rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-teal-700 focus:outline-none placeholder-slate-400"
          />
          {searchQuery && (
            <button
              onClick={() => updateFilter('search', '')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Indicative Quote Disclaimer Notice */}
      <div className="bg-amber-50/70 border border-amber-200/80 rounded-xl p-3.5 flex items-start gap-3 text-xs text-amber-950">
        <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="font-semibold">Indicative Pricing Note:</strong> All premiums displayed are standard illustrative quotes for ₹10L cover (30 yr old male, Bangalore, non-smoker, excluding GST). Final underwriting quotes depend upon individual age, pin code, dependents, and medical history disclosures.
        </p>
      </div>

      {/* Main Layout: Sidebar Filters + Policy Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Filters Sidebar */}
        <aside className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-xs space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-1.5 font-bold text-slate-800 text-xs uppercase tracking-wider">
                <SlidersHorizontal className="w-4 h-4 text-teal-700" />
                <span>Filters</span>
              </div>
              <button
                onClick={handleResetFilters}
                className="text-[11px] font-semibold text-teal-700 hover:underline flex items-center gap-1 cursor-pointer"
              >
                <RotateCcw className="w-3 h-3" /> Reset
              </button>
            </div>

            {/* Category Filter */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700 block">Category</label>
              <select
                value={categoryFilter}
                onChange={(e) => updateFilter('category', e.target.value)}
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-800 focus:ring-1 focus:ring-teal-700"
              >
                <option value="all">All Categories</option>
                {categories.map((c) => (
                  <option key={c.slug} value={c.slug}>{c.name}</option>
                ))}
              </select>
            </div>

            {/* Insurer Filter */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700 block">Insurance Provider</label>
              <select
                value={insurerFilter}
                onChange={(e) => updateFilter('insurer', e.target.value)}
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-800 focus:ring-1 focus:ring-teal-700"
              >
                <option value="all">All Insurers</option>
                {insurers.map((i) => (
                  <option key={i.slug} value={i.slug}>
                    {i.short_name || i.name} {i.claim_settlement_ratio ? `(CSR: ${i.claim_settlement_ratio}%)` : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Sum Insured Filter */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700 block">Minimum Sum Insured</label>
              <select
                value={minSumInsuredFilter}
                onChange={(e) => updateFilter('min_sum_insured', e.target.value)}
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-800 focus:ring-1 focus:ring-teal-700"
              >
                <option value="">Any Sum Insured</option>
                <option value="500000">₹5 Lakhs or more</option>
                <option value="1000000">₹10 Lakhs or more</option>
                <option value="2500000">₹25 Lakhs or more</option>
                <option value="5000000">₹50 Lakhs or more</option>
                <option value="10000000">₹1 Crore or more</option>
              </select>
            </div>

            {/* Annual Budget Range */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <label className="font-semibold text-slate-700">Max Annual Budget</label>
                <span className="text-teal-800 font-bold">
                  {maxBudgetFilter ? `₹${parseInt(maxBudgetFilter).toLocaleString('en-IN')}` : 'Any'}
                </span>
              </div>
              <input
                type="range"
                min="5000"
                max="30000"
                step="1000"
                value={maxBudgetFilter || 30000}
                onChange={(e) => updateFilter('max_budget', e.target.value)}
                className="w-full accent-teal-700 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>₹5,000</span>
                <span>₹30,000+</span>
              </div>
            </div>

            {/* Critical Protection Toggles */}
            <div className="pt-2 border-t border-slate-100 space-y-3">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                Crucial Protections
              </span>

              <label className="flex items-center gap-2.5 text-xs text-slate-700 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={zeroCopayFilter}
                  onChange={(e) => updateFilter('zero_copay', e.target.checked)}
                  className="w-4 h-4 rounded text-teal-700 border-slate-300 focus:ring-teal-600 cursor-pointer"
                />
                <span>Zero Co-payment Only</span>
              </label>

              <label className="flex items-center gap-2.5 text-xs text-slate-700 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={noRoomRentFilter}
                  onChange={(e) => updateFilter('no_room_rent', e.target.checked)}
                  className="w-4 h-4 rounded text-teal-700 border-slate-300 focus:ring-teal-600 cursor-pointer"
                />
                <span>No Room Rent Capping</span>
              </label>
            </div>
          </div>
        </aside>

        {/* Policies Content Area */}
        <main className="lg:col-span-3 space-y-4">
          {/* Results Summary & Sorting */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs bg-white p-3.5 rounded-xl border border-slate-200">
            <span className="font-medium text-slate-600">
              Showing <strong className="text-slate-900">{policies.length}</strong> of <strong className="text-slate-900">{total}</strong> verified policies
            </span>

            <div className="flex items-center gap-2">
              <span className="text-slate-500">Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => updateFilter('sort_by', e.target.value)}
                className="p-1.5 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-800 font-medium focus:ring-1 focus:ring-teal-700"
              >
                <option value="popular">Most Popular</option>
                <option value="premium_asc">Premium: Low to High</option>
                <option value="premium_desc">Premium: High to Low</option>
                <option value="csr_desc">Highest Claim Ratio (CSR)</option>
                <option value="sum_insured_desc">Highest Coverage Sum</option>
              </select>
            </div>
          </div>

          {/* Policy Cards Grid */}
          {loading ? (
            <div className="py-20 text-center">
              <div className="w-8 h-8 border-2 border-teal-700 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-xs text-slate-500">Filtering verified policy data...</p>
            </div>
          ) : policies.length === 0 ? (
            <div className="bg-white rounded-2xl p-10 border border-slate-200 text-center space-y-4">
              <AlertCircle className="w-10 h-10 text-teal-700 mx-auto" />
              <div className="space-y-1">
                <h3 className="text-base font-bold text-slate-800">
                  {total === 0 && !searchQuery && categoryFilter === 'all' && insurerFilter === 'all'
                    ? 'No Authentic Policies Ingested Yet'
                    : 'No policies match your filters'}
                </h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                  {total === 0 && !searchQuery && categoryFilter === 'all' && insurerFilter === 'all'
                    ? 'The insurance explorer displays authentic policy documents collected from approved sources. Use the Ingestion portal to upload official policy wordings or scrape insurer disclosures.'
                    : 'Try widening your budget, adjusting the sum insured, or clearing specific room rent restrictions.'}
                </p>
              </div>
              <div>
                {total === 0 && !searchQuery && categoryFilter === 'all' && insurerFilter === 'all' ? (
                  <button
                    onClick={() => navigate('/admin')}
                    className="px-4 py-2 bg-teal-800 text-white rounded-xl text-xs font-semibold hover:bg-teal-900 cursor-pointer transition-colors shadow-xs"
                  >
                    Go to Data Ingestion Portal
                  </button>
                ) : (
                  <button
                    onClick={handleResetFilters}
                    className="px-4 py-2 bg-teal-800 text-white rounded-xl text-xs font-semibold hover:bg-teal-900 cursor-pointer transition-colors shadow-xs"
                  >
                    Reset All Filters
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {policies.map((p) => (
                <PolicyCard
                  key={p.id}
                  policy={p}
                />
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
