import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import {
  Database,
  Upload,
  Globe,
  FileText,
  CheckCircle,
  AlertCircle,
  HardDrive,
  ShieldCheck,
  ShieldAlert,
  Lock,
  ExternalLink,
  RefreshCw,
  Clock,
  Play,
  Radar,
  PackagePlus,
  GitMerge,
  BellRing,
  SquarePen,
  ListFilter,
  ArrowRight,
  TrendingUp,
  XCircle,
  Info,
  Eye,
  RotateCcw,
  Sparkles,
  Zap,
  Cpu,
  Layers
} from 'lucide-react';

// ─── Status Badge Component ─────────────────────────────────────────────────
const StatusBadge = ({ status }) => {
  const map = {
    CURRENT:      { cls: 'bg-emerald-50 text-emerald-800 border-emerald-200', label: 'CURRENT' },
    WITHDRAWN:    { cls: 'bg-rose-50 text-rose-800 border-rose-200', label: 'WITHDRAWN' },
    NEEDS_REVIEW: { cls: 'bg-amber-50 text-amber-800 border-amber-200', label: 'NEEDS REVIEW' },
    SUPERSEDED:   { cls: 'bg-slate-100 text-slate-600 border-slate-200', label: 'SUPERSEDED' },
  };
  const s = map[status] || { cls: 'bg-slate-100 text-slate-600 border-slate-200', label: status };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded border text-[10px] font-bold ${s.cls}`}>
      {s.label}
    </span>
  );
};

// ─── Job Status Badge ────────────────────────────────────────────────────────
const JobStatusBadge = ({ status }) => {
  if (status === 'BLOCKED_NO_PERMISSION')
    return <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 text-[10px] font-bold">BLOCKED</span>;
  if (status === 'COMPLETED')
    return <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-bold">COMPLETED</span>;
  if (status === 'RUNNING')
    return <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 text-[10px] font-bold">RUNNING</span>;
  if (status === 'FAILED')
    return <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 text-[10px] font-bold">FAILED</span>;
  return <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-bold">{status}</span>;
};

// ─── Provider Slug → Human Readable Name ────────────────────────────────────
const KNOWN_PROVIDERS = {
  'niva-bupa-health-insurance-company-limited': 'Niva Bupa Health Insurance',
  'star-health-and-allied-insurance-company-limited': 'Star Health & Allied Insurance',
  'hdfc-ergo-general-insurance-company-ltd': 'HDFC ERGO General Insurance',
  'the-new-india-assurance-company-limited': 'The New India Assurance',
  'icici-lombard': 'ICICI Lombard',
  'policybazaar': 'PolicyBazaar',
  'irdai': 'IRDAI',
  'shriram-general-insurance-co-ltd': 'Shriram General Insurance',
  'sbi-life-insurance-company-limited': 'SBI Life Insurance',
  'bajaj-allianz-general-insurance-co-ltd': 'Bajaj Allianz General Insurance',
  'care-health-insurance-limited': 'Care Health Insurance',
  'unknown': 'Unknown Provider',
};

const formatProviderSlug = (slug) => {
  if (!slug) return 'Unknown';
  if (KNOWN_PROVIDERS[slug]) return KNOWN_PROVIDERS[slug];
  // Title-case the slug as fallback
  return slug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
};


export const AdminPage = () => {
  // ── Ingestion pipeline state ───────────────────────────────────────────────
  const [status, setStatus] = useState(null);
  const [sources, setSources] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  // ── Market Watch state ─────────────────────────────────────────────────────
  const [marketData, setMarketData] = useState(null);
  const [marketLoading, setMarketLoading] = useState(false);
  const [marketScanning, setMarketScanning] = useState(false);
  const [marketTab, setMarketTab] = useState('discoveries'); // discoveries | revisions | alerts | inventory
  const [selectedItems, setSelectedItems] = useState([]);   // UINs chosen for bulk ingest
  const [applyingUpdates, setApplyingUpdates] = useState(false);
  const [applyResult, setApplyResult] = useState(null);
  const [statusUpdating, setStatusUpdating] = useState(null); // policy_id being updated
  const [inventorySearch, setInventorySearch] = useState('');
  const [inventoryCategoryFilter, setInventoryCategoryFilter] = useState('all');

  // ── Upload / Scrape form state ─────────────────────────────────────────────
  const [uploadFile, setUploadFile] = useState(null);
  const [docTitle, setDocTitle] = useState('');
  const [insurerName, setInsurerName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  const [scrapeUrl, setScrapeUrl] = useState('');
  const [scrapeTitle, setScrapeTitle] = useState('');
  const [scrapeInsurer, setScrapeInsurer] = useState('');
  const [scraping, setScraping] = useState(false);
  const [scrapeSuccess, setScrapeSuccess] = useState(null);
  const [scrapeError, setScrapeError] = useState(null);

  const [jobTriggering, setJobTriggering] = useState(null);
  const [actionNotice, setActionNotice] = useState(null);

  // ── AI Model Retraining Pipeline State ─────────────────────────────────────
  const [retrainData, setRetrainData] = useState(null);
  const [retrainLoading, setRetrainLoading] = useState(false);
  const [retrainTriggering, setRetrainTriggering] = useState(false);
  const [retrainNotice, setRetrainNotice] = useState(null);

  const fetchRetrainStatus = useCallback(async () => {
    try {
      setRetrainLoading(true);
      const data = await api.getRetrainStatus();
      setRetrainData(data);
    } catch (err) {
      console.error('Failed to load retrain status:', err);
    } finally {
      setRetrainLoading(false);
    }
  }, []);

  const handleTriggerRetrain = async () => {
    setRetrainTriggering(true);
    setRetrainNotice(null);
    try {
      const res = await api.triggerRetrainPipeline();
      setRetrainNotice({ type: 'success', message: res.message });
      await fetchRetrainStatus();
    } catch (err) {
      setRetrainNotice({ type: 'error', message: err.message });
    } finally {
      setRetrainTriggering(false);
    }
  };

  const handleToggleAutoRetrain = async (enabled) => {
    try {
      const updated = await api.updateRetrainConfig({ enabled });
      setRetrainData(updated);
    } catch (err) {
      console.error('Failed to toggle auto retrain:', err);
    }
  };

  const handleUpdateCadence = async (cadenceDays) => {
    try {
      const updated = await api.updateRetrainConfig({ cadence_days: Number(cadenceDays) });
      setRetrainData(updated);
    } catch (err) {
      console.error('Failed to update cadence:', err);
    }
  };

  // ── Fetch pipeline data ────────────────────────────────────────────────────
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [statusData, sourcesData, jobsData] = await Promise.all([
        api.getIngestionStatus().catch(() => null),
        api.getSourceRegistries().catch(() => []),
        api.getIngestionJobs().catch(() => [])
      ]);
      setStatus(statusData);
      setSources(sourcesData || []);
      setJobs(jobsData || []);
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Fetch market watch data (lazy: only on demand / initial load) ──────────
  const fetchMarketData = useCallback(async () => {
    setMarketLoading(true);
    try {
      const data = await api.getMarketUpdates();
      setMarketData(data);
      setSelectedItems([]);
      setApplyResult(null);
    } catch (err) {
      console.error('Failed to fetch market data:', err);
    } finally {
      setMarketLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    fetchMarketData();
    fetchRetrainStatus();
  }, [fetchData, fetchMarketData, fetchRetrainStatus]);

  // Poll retrain status while active pipeline is in progress
  useEffect(() => {
    if (retrainData?.current_status && !['IDLE', 'COMPLETED', 'FAILED'].includes(retrainData.current_status)) {
      const pollTimer = setInterval(fetchRetrainStatus, 4000);
      return () => clearInterval(pollTimer);
    }
  }, [retrainData?.current_status, fetchRetrainStatus]);

  // ── Market Scan (on-demand rescan button) ─────────────────────────────────
  const handleMarketScan = async () => {
    setMarketScanning(true);
    setApplyResult(null);
    try {
      const data = await api.scanMarketUpdates();
      setMarketData(data);
      setSelectedItems([]);
    } catch (err) {
      console.error('Scan failed:', err);
    } finally {
      setMarketScanning(false);
    }
  };

  // ── Toggle select item for batch ingest ──────────────────────────────────
  const toggleSelectItem = (uin) => {
    setSelectedItems(prev =>
      prev.includes(uin) ? prev.filter(u => u !== uin) : [...prev, uin]
    );
  };

  const selectAllDiscoveries = () => {
    if (!marketData) return;
    const allUins = marketData.new_discoveries.map(d => d.uin);
    setSelectedItems(prev =>
      prev.length === allUins.length ? [] : allUins
    );
  };

  // ── Apply selected market updates ─────────────────────────────────────────
  const handleApplyUpdates = async () => {
    if (selectedItems.length === 0 || !marketData) return;
    setApplyingUpdates(true);
    setApplyResult(null);
    try {
      const items = selectedItems.map(uin => {
        const disc = marketData.new_discoveries.find(d => d.uin === uin);
        return disc ? { ...disc, action_type: 'INGEST_NEW' } : null;
      }).filter(Boolean);

      const result = await api.applyMarketUpdates(items, 'Admin');
      setApplyResult({ type: 'success', ...result });
      await fetchMarketData();
      await fetchData();
    } catch (err) {
      setApplyResult({ type: 'error', message: err.message });
    } finally {
      setApplyingUpdates(false);
    }
  };

  // ── Update policy status ──────────────────────────────────────────────────
  const handleUpdateStatus = async (policyId, newStatus, reason = null) => {
    setStatusUpdating(policyId);
    try {
      await api.updatePolicyStatus(policyId, newStatus, reason);
      // Refresh market data to show updated inventory
      await fetchMarketData();
      setActionNotice({
        type: 'success',
        title: 'Status Updated',
        message: `Policy status changed to ${newStatus} and persisted to database.`
      });
    } catch (err) {
      setActionNotice({ type: 'error', title: 'Update Failed', message: err.message });
    } finally {
      setStatusUpdating(null);
    }
  };

  // ── Manual Upload ─────────────────────────────────────────────────────────
  const handleManualUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;
    setUploading(true);
    setUploadSuccess(null);
    setUploadError(null);
    const formData = new FormData();
    formData.append('file', uploadFile);
    if (docTitle) formData.append('title', docTitle);
    if (insurerName) formData.append('insurer_name', insurerName);
    try {
      const res = await api.uploadDocument(formData);
      setUploadSuccess(`"${res.title}" indexed into ${res.chunk_count} RAG chunks with SHA-256 verification!`);
      setUploadFile(null);
      setDocTitle('');
      setInsurerName('');
      fetchData();
    } catch (err) {
      setUploadError(err.message || 'Upload and parsing failed');
    } finally {
      setUploading(false);
    }
  };

  // ── URL Scrape ────────────────────────────────────────────────────────────
  const handleScrapeUrl = async (e) => {
    e.preventDefault();
    if (!scrapeUrl) return;
    setScraping(true);
    setScrapeSuccess(null);
    setScrapeError(null);
    try {
      const res = await api.scrapeUrl(scrapeUrl, scrapeTitle || 'Web Disclosure', scrapeInsurer);
      setScrapeSuccess(`URL scraped and indexed into ${res.chunk_count} RAG chunks!`);
      setScrapeUrl('');
      setScrapeTitle('');
      setScrapeInsurer('');
      fetchData();
    } catch (err) {
      setScrapeError(err.message || 'Scraping failed');
      fetchData();
    } finally {
      setScraping(false);
    }
  };

  // ── Trigger Source ingestion ──────────────────────────────────────────────
  const handleTriggerSource = async (sourceId, sourceName) => {
    setJobTriggering(sourceId);
    setActionNotice(null);
    try {
      const res = await api.runIngestionJob({ source_id: sourceId, job_type: 'FETCH_DOC' });
      if (res.status === 'BLOCKED_NO_PERMISSION') {
        setActionNotice({
          type: 'blocked',
          title: 'Ingestion Blocked by Authorization Policy',
          message: `"${sourceName}" is registered as "link_only". ${res.failure_details || 'Automated scraping requires written authorization.'}`
        });
      } else {
        setActionNotice({
          type: 'success',
          title: 'Job Dispatched',
          message: `Job ${res.id} queued with status: ${res.status}`
        });
      }
      fetchData();
    } catch (err) {
      setActionNotice({ type: 'error', title: 'Execution Error', message: err.message });
      fetchData();
    } finally {
      setJobTriggering(null);
    }
  };

  // ── Inventory derived data ─────────────────────────────────────────────────
  const filteredInventory = (marketData?.inventory || []).filter(p => {
    const matchesSearch = !inventorySearch ||
      p.name.toLowerCase().includes(inventorySearch.toLowerCase()) ||
      p.insurer_name.toLowerCase().includes(inventorySearch.toLowerCase()) ||
      (p.uin_number || '').toLowerCase().includes(inventorySearch.toLowerCase());
    const matchesCat = inventoryCategoryFilter === 'all' || p.category_slug === inventoryCategoryFilter;
    return matchesSearch && matchesCat;
  });

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">

      {/* ── Page Header ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-800">
              Admin &amp; Data Pipeline
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight mt-1">
            Data Ingestion &amp; Source Governance
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Market policy watch, ingestion control, source compliance, and lifecycle management.
          </p>
        </div>
        <button
          onClick={() => { fetchData(); fetchMarketData(); }}
          disabled={loading || marketLoading}
          className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors self-start sm:self-auto cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${(loading || marketLoading) ? 'animate-spin' : ''}`} />
          <span>Refresh All</span>
        </button>
      </div>

      {/* ── Global Action Notification Banner ────────────────────────────────── */}
      {actionNotice && (
        <div className={`p-4 rounded-2xl border text-xs flex items-start gap-3 ${
          actionNotice.type === 'blocked'
            ? 'bg-amber-50 border-amber-200 text-amber-950'
            : actionNotice.type === 'error'
            ? 'bg-rose-50 border-rose-200 text-rose-950'
            : 'bg-emerald-50 border-emerald-200 text-emerald-950'
        }`}>
          {actionNotice.type === 'blocked' ? (
            <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          ) : actionNotice.type === 'error' ? (
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          ) : (
            <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          )}
          <div className="space-y-0.5 flex-1">
            <h4 className="font-bold">{actionNotice.title}</h4>
            <p className="text-slate-600 leading-relaxed">{actionNotice.message}</p>
          </div>
          <button onClick={() => setActionNotice(null)} className="shrink-0 cursor-pointer">
            <XCircle className="w-4 h-4 text-slate-400 hover:text-slate-700" />
          </button>
        </div>
      )}

      {/* ── Overview Stats ────────────────────────────────────────────────────── */}
      {status && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Indexed Sources</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-extrabold text-slate-900">{status.total_sources}</span>
              <span className="text-xs text-slate-500">PDFs / Disclosures</span>
            </div>
          </div>
          <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">RAG Chunks</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-extrabold text-teal-800">{status.total_chunks}</span>
              <span className="text-xs text-slate-500">Indexed Sections</span>
            </div>
          </div>
          <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Active Policies</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-extrabold text-indigo-700">{marketData?.inventory_count ?? '—'}</span>
              <span className="text-xs text-slate-500">In Database</span>
            </div>
          </div>
          <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Pending Ingest</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className={`text-2xl font-extrabold ${(marketData?.new_discoveries_count ?? 0) > 0 ? 'text-amber-700' : 'text-slate-900'}`}>
                {marketData?.new_discoveries_count ?? '—'}
              </span>
              <span className="text-xs text-slate-500">Discoveries</span>
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════════
          SECTION 1: MARKET WATCH & POLICY UPDATE CONTROL CENTER
      ══════════════════════════════════════════════════════════════════════ */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
        {/* Header */}
        <div className="px-6 sm:px-8 py-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-50 flex items-center justify-center">
              <Radar className="w-5 h-5 text-indigo-700" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Market Watch &amp; Policy Update Control Center</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Continuously monitors IRDAI catalogue and insurer portals. Detects new filings, version revisions, and archive alerts.
              </p>
            </div>
          </div>
          <button
            onClick={handleMarketScan}
            disabled={marketScanning || marketLoading}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white rounded-xl text-xs font-semibold transition-colors cursor-pointer shadow-sm shrink-0"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${marketScanning ? 'animate-spin' : ''}`} />
            <span>{marketScanning ? 'Scanning Market...' : 'Scan Market Now'}</span>
          </button>
        </div>

        {/* Apply Result Banner */}
        {applyResult && (
          <div className={`mx-6 sm:mx-8 mt-5 p-4 rounded-xl border text-xs flex items-start gap-3 ${
            applyResult.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-950'
              : 'bg-rose-50 border-rose-200 text-rose-950'
          }`}>
            {applyResult.type === 'success'
              ? <CheckCircle className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
              : <AlertCircle className="w-4 h-4 text-rose-700 shrink-0 mt-0.5" />
            }
            <div>
              {applyResult.type === 'success' ? (
                <>
                  <strong>Market update applied successfully!</strong>
                  <span className="ml-2">{applyResult.created_count} new policies ingested, {applyResult.updated_count} revised.</span>
                </>
              ) : (
                <><strong>Apply failed:</strong> {applyResult.message}</>
              )}
            </div>
          </div>
        )}

        {/* Scan Summary Pills */}
        {marketData && (
          <div className="px-6 sm:px-8 pt-5 pb-0 flex flex-wrap gap-3">
            <button
              onClick={() => setMarketTab('discoveries')}
              className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
                marketTab === 'discoveries'
                  ? 'bg-amber-100 text-amber-800 border border-amber-300'
                  : 'bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100'
              }`}
            >
              <PackagePlus className="w-3.5 h-3.5" />
              <span>New Discoveries</span>
              <span className={`ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                marketData.new_discoveries_count > 0
                  ? 'bg-amber-700 text-white'
                  : 'bg-slate-200 text-slate-600'
              }`}>{marketData.new_discoveries_count}</span>
            </button>
            <button
              onClick={() => setMarketTab('revisions')}
              className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
                marketTab === 'revisions'
                  ? 'bg-blue-100 text-blue-800 border border-blue-300'
                  : 'bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100'
              }`}
            >
              <GitMerge className="w-3.5 h-3.5" />
              <span>Revisions</span>
              <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 text-slate-600">
                {marketData.revisions_count}
              </span>
            </button>
            <button
              onClick={() => setMarketTab('alerts')}
              className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
                marketTab === 'alerts'
                  ? 'bg-rose-100 text-rose-800 border border-rose-300'
                  : 'bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100'
              }`}
            >
              <BellRing className="w-3.5 h-3.5" />
              <span>Status Alerts</span>
              <span className={`ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                marketData.alerts_count > 0
                  ? 'bg-rose-700 text-white'
                  : 'bg-slate-200 text-slate-600'
              }`}>{marketData.alerts_count}</span>
            </button>
            <button
              onClick={() => setMarketTab('inventory')}
              className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
                marketTab === 'inventory'
                  ? 'bg-teal-100 text-teal-800 border border-teal-300'
                  : 'bg-slate-50 text-slate-600 border border-slate-200 hover:bg-slate-100'
              }`}
            >
              <ListFilter className="w-3.5 h-3.5" />
              <span>Policy Inventory</span>
              <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 text-slate-600">
                {marketData.inventory_count}
              </span>
            </button>
            {marketData.scanned_at && (
              <span className="ml-auto text-[11px] text-slate-400 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Last scan: {new Date(marketData.scanned_at).toLocaleTimeString()}
              </span>
            )}
          </div>
        )}

        {/* ── Tab Content ─────────────────────────────────────────────────────── */}
        <div className="px-6 sm:px-8 py-6">

          {/* Loading state */}
          {(marketLoading || marketScanning) && (
            <div className="py-16 flex flex-col items-center gap-3 text-slate-500">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-500" />
              <span className="text-sm font-medium">{marketScanning ? 'Scanning IRDAI catalogue & registered insurer portals...' : 'Loading market data...'}</span>
            </div>
          )}

          {!marketLoading && !marketScanning && marketData && (

            <>
              {/* ── TAB: New Discoveries ─────────────────────────────────── */}
              {marketTab === 'discoveries' && (
                <div className="space-y-4">
                  {marketData.new_discoveries.length === 0 ? (
                    <div className="py-12 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
                      <CheckCircle className="w-8 h-8 text-emerald-400" />
                      <span>All market products are already ingested. No new discoveries found.</span>
                    </div>
                  ) : (
                    <>
                      {/* Batch action bar */}
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-amber-50 border border-amber-200 rounded-2xl">
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={selectedItems.length === marketData.new_discoveries.length}
                            onChange={selectAllDiscoveries}
                            className="rounded w-4 h-4 accent-indigo-600 cursor-pointer"
                          />
                          <span className="text-xs font-semibold text-amber-900">
                            {selectedItems.length > 0
                              ? `${selectedItems.length} of ${marketData.new_discoveries.length} selected`
                              : `${marketData.new_discoveries.length} new policies discovered in market`}
                          </span>
                        </div>
                        <button
                          onClick={handleApplyUpdates}
                          disabled={selectedItems.length === 0 || applyingUpdates}
                          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl text-xs font-semibold transition-colors cursor-pointer shadow-sm"
                        >
                          <PackagePlus className="w-3.5 h-3.5" />
                          <span>
                            {applyingUpdates
                              ? 'Ingesting...'
                              : selectedItems.length > 0
                              ? `Approve & Ingest ${selectedItems.length} Policy${selectedItems.length > 1 ? 'ies' : ''}`
                              : 'Select policies to ingest'}
                          </span>
                        </button>
                      </div>

                      {/* Discovery table */}
                      <div className="overflow-x-auto overflow-y-auto max-h-[420px] rounded-xl border border-slate-200">
                        <table className="w-full text-left text-xs min-w-[750px]">
                          <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 sticky top-0 z-10">
                            <tr>
                              <th className="p-3 w-8"></th>
                              <th className="p-3">Product Name & UIN</th>
                              <th className="p-3">Insurer</th>
                              <th className="p-3">Category</th>
                              <th className="p-3">IRDAI Approved</th>
                              <th className="p-3">Archive Status</th>
                              <th className="p-3 text-right">Action</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {marketData.new_discoveries.map((disc) => (
                              <tr key={disc.uin} className={`hover:bg-slate-50/60 transition-colors ${selectedItems.includes(disc.uin) ? 'bg-indigo-50/40' : ''}`}>
                                <td className="p-3">
                                  <input
                                    type="checkbox"
                                    checked={selectedItems.includes(disc.uin)}
                                    onChange={() => toggleSelectItem(disc.uin)}
                                    className="rounded w-3.5 h-3.5 accent-indigo-600 cursor-pointer"
                                  />
                                </td>
                                <td className="p-3">
                                  <div className="font-semibold text-slate-900">{disc.product_name}</div>
                                  <div className="font-mono text-[10px] text-slate-400 mt-0.5">{disc.uin}</div>
                                </td>
                                <td className="p-3 text-slate-700">{disc.insurer_name}</td>
                                <td className="p-3">
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                                    disc.category_slug === 'health' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' :
                                    disc.category_slug === 'motor' ? 'bg-blue-50 text-blue-800 border-blue-200' :
                                    disc.category_slug === 'travel' ? 'bg-purple-50 text-purple-800 border-purple-200' :
                                    'bg-slate-100 text-slate-700 border-slate-200'
                                  }`}>
                                    {disc.category_slug.toUpperCase()}
                                  </span>
                                </td>
                                <td className="p-3 text-slate-600">{disc.approval_date || '—'}</td>
                                <td className="p-3">
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                    disc.archive_status === 'Non-Archived'
                                      ? 'bg-emerald-50 text-emerald-700'
                                      : 'bg-amber-50 text-amber-700'
                                  }`}>
                                    {disc.archive_status}
                                  </span>
                                </td>
                                <td className="p-3 text-right">
                                  {disc.document_url && (
                                    <a
                                      href={disc.document_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[10px] font-semibold transition-colors"
                                    >
                                      <Eye className="w-3 h-3" />
                                      View PDF
                                    </a>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* ── TAB: Revisions ───────────────────────────────────────── */}
              {marketTab === 'revisions' && (
                <div className="space-y-4">
                  {marketData.revisions.length === 0 ? (
                    <div className="py-12 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
                      <GitMerge className="w-8 h-8 text-slate-300" />
                      <span>No version revisions detected. All products match current database versions.</span>
                    </div>
                  ) : (
                    <div className="overflow-x-auto overflow-y-auto max-h-[420px] rounded-xl border border-slate-200">
                      <table className="w-full text-left text-xs min-w-[750px]">
                        <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 sticky top-0 z-10">
                          <tr>
                            <th className="p-3">Existing Policy</th>
                            <th className="p-3">Old UIN / Version</th>
                            <th className="p-3">New UIN / Version</th>
                            <th className="p-3">IRDAI Filed</th>
                            <th className="p-3">Summary</th>
                            <th className="p-3 text-right">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {marketData.revisions.map((rev, i) => (
                            <tr key={i} className="hover:bg-slate-50/60">
                              <td className="p-3">
                                <div className="font-semibold text-slate-900">{rev.existing_policy_name}</div>
                                <div className="text-slate-500 text-[11px]">{rev.insurer_name}</div>
                              </td>
                              <td className="p-3 font-mono text-[10px] text-slate-500">
                                {rev.existing_uin} ({rev.existing_version})
                              </td>
                              <td className="p-3 font-mono text-[10px] text-blue-700 font-semibold">
                                {rev.new_uin} ({rev.new_version})
                              </td>
                              <td className="p-3 text-slate-600">{rev.approval_date}</td>
                              <td className="p-3 text-slate-600 max-w-xs">{rev.diff_summary}</td>
                              <td className="p-3 text-right">
                                <button
                                  onClick={() => api.applyMarketUpdates([{ ...rev, action_type: 'APPLY_REVISION', policy_id: rev.existing_policy_id }]).then(fetchMarketData)}
                                  className="px-2.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-[10px] font-semibold transition-colors cursor-pointer"
                                >
                                  Apply Revision
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* ── TAB: Status Alerts ───────────────────────────────────── */}
              {marketTab === 'alerts' && (
                <div className="space-y-4">
                  {marketData.status_alerts.length === 0 ? (
                    <div className="py-12 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
                      <CheckCircle className="w-8 h-8 text-emerald-400" />
                      <span>No status discrepancies detected. All products' lifecycle statuses are in sync.</span>
                    </div>
                  ) : (
                    <div className="overflow-x-auto overflow-y-auto max-h-[420px] rounded-xl border border-slate-200">
                      <table className="w-full text-left text-xs min-w-[750px]">
                        <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 sticky top-0 z-10">
                          <tr>
                            <th className="p-3">Policy</th>
                            <th className="p-3">UIN</th>
                            <th className="p-3">DB Status</th>
                            <th className="p-3">Recommended Action</th>
                            <th className="p-3">Reason</th>
                            <th className="p-3 text-right">Apply</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {marketData.status_alerts.map((alert, i) => (
                            <tr key={i} className="hover:bg-slate-50/60">
                              <td className="p-3 font-semibold text-slate-900">{alert.policy_name}</td>
                              <td className="p-3 font-mono text-[10px] text-slate-500">{alert.uin}</td>
                              <td className="p-3"><StatusBadge status={alert.current_status} /></td>
                              <td className="p-3"><StatusBadge status={alert.recommended_status} /></td>
                              <td className="p-3 text-slate-600 max-w-xs text-[11px]">{alert.reason}</td>
                              <td className="p-3 text-right">
                                <button
                                  onClick={() => handleUpdateStatus(alert.policy_id, alert.recommended_status, alert.reason)}
                                  disabled={statusUpdating === alert.policy_id}
                                  className="px-2.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 disabled:opacity-60 text-white text-[10px] font-semibold cursor-pointer transition-colors"
                                >
                                  {statusUpdating === alert.policy_id ? '...' : 'Apply Status'}
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* ── TAB: Policy Inventory (Status Manager) ───────────────── */}
              {marketTab === 'inventory' && (
                <div className="space-y-4">
                  {/* Filters */}
                  <div className="flex flex-col sm:flex-row gap-3">
                    <div className="relative flex-1">
                      <input
                        type="text"
                        placeholder="Search by name, insurer, or UIN..."
                        value={inventorySearch}
                        onChange={e => setInventorySearch(e.target.value)}
                        className="w-full pl-3 pr-8 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 placeholder-slate-400"
                      />
                    </div>
                    <select
                      value={inventoryCategoryFilter}
                      onChange={e => setInventoryCategoryFilter(e.target.value)}
                      className="px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 cursor-pointer"
                    >
                      <option value="all">All Categories</option>
                      <option value="health">Health</option>
                      <option value="term-life">Term Life</option>
                      <option value="motor">Motor</option>
                      <option value="travel">Travel</option>
                    </select>
                  </div>

                  <div className="overflow-x-auto overflow-y-auto max-h-[420px] rounded-xl border border-slate-200">
                    <table className="w-full text-left text-xs min-w-[700px]">
                      <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 sticky top-0 z-10">
                        <tr>
                          <th className="p-3">Policy</th>
                          <th className="p-3">Insurer</th>
                          <th className="p-3">Category</th>
                          <th className="p-3">UIN</th>
                          <th className="p-3">Facts</th>
                          <th className="p-3">Status</th>
                          <th className="p-3 text-right">Controls</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {filteredInventory.map((pol) => (
                          <tr key={pol.id} className="hover:bg-slate-50/60 transition-colors">
                            <td className="p-3">
                              <Link
                                to={`/policies/${pol.slug}`}
                                className="font-semibold text-slate-900 hover:text-teal-700 transition-colors"
                              >
                                {pol.name}
                              </Link>
                            </td>
                            <td className="p-3 text-slate-600">{pol.insurer_name}</td>
                            <td className="p-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                pol.category_slug === 'health' ? 'bg-emerald-50 text-emerald-700' :
                                pol.category_slug === 'motor' ? 'bg-blue-50 text-blue-700' :
                                pol.category_slug === 'travel' ? 'bg-purple-50 text-purple-700' :
                                'bg-slate-100 text-slate-600'
                              }`}>
                                {pol.category_name}
                              </span>
                            </td>
                            <td className="p-3 font-mono text-[10px] text-slate-400">{pol.uin_number}</td>
                            <td className="p-3">
                              <span className={`font-semibold ${pol.facts_count > 0 ? 'text-teal-700' : 'text-slate-400'}`}>
                                {pol.facts_count}
                              </span>
                            </td>
                            <td className="p-3"><StatusBadge status={pol.status} /></td>
                            <td className="p-3 text-right">
                              <div className="flex items-center justify-end gap-1.5">
                                {pol.status !== 'CURRENT' && (
                                  <button
                                    onClick={() => handleUpdateStatus(pol.id, 'CURRENT', 'Admin restored to current')}
                                    disabled={statusUpdating === pol.id}
                                    className="px-2 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:opacity-60 text-white text-[10px] font-semibold cursor-pointer transition-colors"
                                    title="Set to CURRENT"
                                  >
                                    {statusUpdating === pol.id ? '...' : 'Set Current'}
                                  </button>
                                )}
                                {pol.status !== 'NEEDS_REVIEW' && (
                                  <button
                                    onClick={() => handleUpdateStatus(pol.id, 'NEEDS_REVIEW', 'Flagged for manual review')}
                                    disabled={statusUpdating === pol.id}
                                    className="px-2 py-1 rounded-lg bg-amber-500 hover:bg-amber-600 disabled:opacity-60 text-white text-[10px] font-semibold cursor-pointer transition-colors"
                                    title="Flag for Review"
                                  >
                                    {statusUpdating === pol.id ? '...' : 'Flag Review'}
                                  </button>
                                )}
                                {pol.status !== 'WITHDRAWN' && (
                                  <button
                                    onClick={() => handleUpdateStatus(pol.id, 'WITHDRAWN', 'Admin marked as withdrawn')}
                                    disabled={statusUpdating === pol.id}
                                    className="px-2 py-1 rounded-lg bg-rose-600 hover:bg-rose-700 disabled:opacity-60 text-white text-[10px] font-semibold cursor-pointer transition-colors"
                                    title="Mark as Withdrawn"
                                  >
                                    {statusUpdating === pol.id ? '...' : 'Withdraw'}
                                  </button>
                                )}
                                <Link
                                  to={`/policies/${pol.slug}`}
                                  className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 transition-colors"
                                  title="View Policy Page"
                                >
                                  <ArrowRight className="w-3 h-3" />
                                </Link>
                              </div>
                            </td>
                          </tr>
                        ))}
                        {filteredInventory.length === 0 && (
                          <tr>
                            <td colSpan={7} className="p-8 text-center text-xs text-slate-400">
                              No policies match the current filters.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Initial empty state if no scan done */}
          {!marketLoading && !marketScanning && !marketData && (
            <div className="py-16 text-center flex flex-col items-center gap-3">
              <Radar className="w-12 h-12 text-indigo-200" />
              <p className="text-sm font-medium text-slate-600">Click "Scan Market Now" to detect new policies and revisions</p>
            </div>
          )}
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          SECTION 2: AI MODEL RETRAINING & CLOUDFLARE EDGE PIPELINE
      ══════════════════════════════════════════════════════════════════════ */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden space-y-6 p-6 sm:p-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-teal-50 flex items-center justify-center border border-teal-100 shrink-0">
              <Cpu className="w-5 h-5 text-teal-700" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900">AI Model Retraining &amp; Cloudflare Edge Pipeline</h2>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-teal-50 text-teal-800 font-bold border border-teal-200">
                  1-Month Inbuilt Timer
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Autonomous periodic retraining cycle. Rebuilds training pairs from Postgres, pushes to Kaggle GPU, and synchronizes the Cloudflare Workers AI edge model.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 shrink-0">
            <button
              onClick={fetchRetrainStatus}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
              title="Refresh status"
            >
              <RefreshCw className={`w-4 h-4 ${retrainLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={handleTriggerRetrain}
              disabled={retrainTriggering || (retrainData?.current_status && !['IDLE', 'COMPLETED', 'FAILED'].includes(retrainData.current_status))}
              className="flex items-center gap-2 px-4 py-2.5 bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white rounded-xl text-xs font-semibold transition-all shadow-sm cursor-pointer"
            >
              <Play className={`w-3.5 h-3.5 fill-current ${retrainTriggering ? 'animate-spin' : ''}`} />
              <span>{retrainTriggering ? 'Triggering Pipeline...' : 'Trigger Retrain Now'}</span>
            </button>
          </div>
        </div>

        {/* Retrain Notice Banner if any */}
        {retrainNotice && (
          <div className={`p-3.5 rounded-2xl border text-xs flex items-center justify-between gap-3 ${
            retrainNotice.type === 'error'
              ? 'bg-rose-50 border-rose-200 text-rose-800'
              : 'bg-teal-50 border-teal-200 text-teal-800'
          }`}>
            <div className="flex items-center gap-2">
              {retrainNotice.type === 'error' ? <AlertCircle className="w-4 h-4 shrink-0" /> : <CheckCircle className="w-4 h-4 shrink-0" />}
              <span>{retrainNotice.message}</span>
            </div>
            <button onClick={() => setRetrainNotice(null)} className="text-slate-400 hover:text-slate-600 text-xs cursor-pointer">✕</button>
          </div>
        )}

        {/* Status Metrics Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1">
            <div className="flex items-center justify-between text-[11px] text-slate-400 font-semibold uppercase tracking-wider">
              <span>Edge Model</span>
              <Cpu className="w-3.5 h-3.5 text-teal-600" />
            </div>
            <p className="text-sm font-bold text-slate-800 truncate" title={retrainData?.model_name}>
              {retrainData?.model_name || 'Llama-3.1-8B-fp8 (LoRA r=8)'}
            </p>
            <a
              href={retrainData?.cloudflare_endpoint || 'https://bimagyan-ai.siddharth-bimagyan.workers.dev'}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] text-teal-700 hover:underline flex items-center gap-0.5 truncate"
            >
              Cloudflare Edge Runtime <ExternalLink className="w-2.5 h-2.5" />
            </a>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1">
            <div className="flex items-center justify-between text-[11px] text-slate-400 font-semibold uppercase tracking-wider">
              <span>Pipeline Status</span>
              <Zap className="w-3.5 h-3.5 text-amber-500" />
            </div>
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10.5px] font-bold border ${
                retrainData?.current_status === 'IDLE'
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : retrainData?.current_status === 'FAILED'
                  ? 'bg-rose-50 text-rose-800 border-rose-200'
                  : 'bg-blue-50 text-blue-800 border-blue-200 animate-pulse'
              }`}>
                {retrainData?.current_status || 'IDLE'}
              </span>
            </div>
            <p className="text-[10.5px] text-slate-500 truncate" title={retrainData?.current_step}>
              {retrainData?.current_step || 'Ready for next run'}
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1">
            <div className="flex items-center justify-between text-[11px] text-slate-400 font-semibold uppercase tracking-wider">
              <span>Next Retrain Due</span>
              <Clock className="w-3.5 h-3.5 text-indigo-600" />
            </div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-lg font-extrabold text-slate-900">
                {retrainData?.days_remaining !== undefined ? `${retrainData.days_remaining}d` : '30d'}
              </span>
              <span className="text-[10.5px] text-slate-500">
                ({retrainData?.cadence_days || 30}-day cycle)
              </span>
            </div>
            <p className="text-[10px] text-slate-400">
              {retrainData?.next_run ? new Date(retrainData.next_run).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : 'Next month'}
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1">
            <div className="flex items-center justify-between text-[11px] text-slate-400 font-semibold uppercase tracking-wider">
              <span>Scheduler Mode</span>
              <RotateCcw className="w-3.5 h-3.5 text-teal-600" />
            </div>
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10.5px] font-bold border ${
                retrainData?.enabled
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : 'bg-slate-100 text-slate-600 border-slate-200'
              }`}>
                {retrainData?.enabled ? 'AUTONOMOUS' : 'PAUSED'}
              </span>
            </div>
            <p className="text-[10px] text-slate-400">
              {retrainData?.enabled ? 'Runs every 30 days automatically' : 'Manual triggers only'}
            </p>
          </div>
        </div>

        {/* Cadence & Scheduler Configuration Controls */}
        <div className="p-4 rounded-2xl bg-teal-50/50 border border-teal-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 font-semibold text-slate-700 cursor-pointer">
              <input
                type="checkbox"
                checked={retrainData?.enabled ?? true}
                onChange={(e) => handleToggleAutoRetrain(e.target.checked)}
                className="w-4 h-4 text-teal-700 rounded border-slate-300 focus:ring-teal-600 cursor-pointer"
              />
              <span>Enable Automatic 1-Month Retraining Loop</span>
            </label>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-500">Cadence Interval:</span>
            <select
              value={retrainData?.cadence_days || 30}
              onChange={(e) => handleUpdateCadence(e.target.value)}
              className="px-2.5 py-1.5 rounded-xl bg-white border border-slate-200 text-slate-800 text-xs font-medium focus:ring-2 focus:ring-teal-600 outline-none cursor-pointer"
            >
              <option value="14">Every 14 Days (Bi-weekly)</option>
              <option value="30">Every 30 Days (1 Month - Recommended)</option>
              <option value="60">Every 60 Days (2 Months)</option>
              <option value="90">Every 90 Days (Quarterly)</option>
            </select>
          </div>
        </div>

        {/* Pipeline Step Visualizer */}
        <div className="space-y-2 pt-1">
          <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block">
            Automated Retraining &amp; Edge Sync Stages
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs">
            <div className={`p-3 rounded-xl border flex items-center gap-2.5 ${
              retrainData?.current_status === 'BUILDING_DATASET'
                ? 'bg-blue-50 border-blue-200 text-blue-900 font-semibold ring-1 ring-blue-300'
                : 'bg-slate-50 border-slate-200/80 text-slate-600'
            }`}>
              <span className="w-5 h-5 rounded-full bg-teal-700 text-white flex items-center justify-center text-[10px] font-bold shrink-0">1</span>
              <span className="truncate">Extract Live DB &amp; Export JSONL</span>
            </div>
            <div className={`p-3 rounded-xl border flex items-center gap-2.5 ${
              retrainData?.current_status === 'UPLOADING_KAGGLE'
                ? 'bg-blue-50 border-blue-200 text-blue-900 font-semibold ring-1 ring-blue-300'
                : 'bg-slate-50 border-slate-200/80 text-slate-600'
            }`}>
              <span className="w-5 h-5 rounded-full bg-teal-700 text-white flex items-center justify-center text-[10px] font-bold shrink-0">2</span>
              <span className="truncate">Push Dataset to Kaggle Hub</span>
            </div>
            <div className={`p-3 rounded-xl border flex items-center gap-2.5 ${
              retrainData?.current_status === 'TRIGGERING_KAGGLE'
                ? 'bg-blue-50 border-blue-200 text-blue-900 font-semibold ring-1 ring-blue-300'
                : 'bg-slate-50 border-slate-200/80 text-slate-600'
            }`}>
              <span className="w-5 h-5 rounded-full bg-teal-700 text-white flex items-center justify-center text-[10px] font-bold shrink-0">3</span>
              <span className="truncate">Train LoRA on Kaggle GPU</span>
            </div>
            <div className={`p-3 rounded-xl border flex items-center gap-2.5 ${
              retrainData?.current_status === 'SYNCING_CLOUDFLARE'
                ? 'bg-blue-50 border-blue-200 text-blue-900 font-semibold ring-1 ring-blue-300'
                : 'bg-slate-50 border-slate-200/80 text-slate-600'
            }`}>
              <span className="w-5 h-5 rounded-full bg-teal-700 text-white flex items-center justify-center text-[10px] font-bold shrink-0">4</span>
              <span className="truncate">Deploy &amp; Verify Edge Model</span>
            </div>
          </div>
        </div>

        {/* Retraining History Log */}
        {retrainData?.history && retrainData.history.length > 0 && (
          <div className="space-y-2 pt-2 border-t border-slate-100">
            <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block">
              Recent Retraining Executions
            </span>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs min-w-[600px]">
                <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="p-2.5">Run ID</th>
                    <th className="p-2.5">Date &amp; Time</th>
                    <th className="p-2.5">Trigger Mode</th>
                    <th className="p-2.5">Duration</th>
                    <th className="p-2.5">Status</th>
                    <th className="p-2.5">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {retrainData.history.map((h, hIdx) => (
                    <tr key={hIdx} className="hover:bg-slate-50/60">
                      <td className="p-2.5 font-mono text-[11px] font-medium text-slate-600">{h.id}</td>
                      <td className="p-2.5 whitespace-nowrap text-slate-600">
                        {new Date(h.timestamp).toLocaleString('en-IN', {
                          day: 'numeric', month: 'short', year: 'numeric',
                          hour: '2-digit', minute: '2-digit'
                        })}
                      </td>
                      <td className="p-2.5">
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                          {h.trigger}
                        </span>
                      </td>
                      <td className="p-2.5 font-mono text-[11px] text-slate-500">
                        {h.duration_seconds ? `${h.duration_seconds}s` : '—'}
                      </td>
                      <td className="p-2.5">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          h.status === 'SUCCESS' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-800 border border-rose-200'
                        }`}>
                          {h.status}
                        </span>
                      </td>
                      <td className="p-2.5 text-[11px] text-slate-500 max-w-xs truncate" title={h.details}>
                        {h.details}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          SECTION 3: SOURCE REGISTRY & COMPLIANCE GOVERNANCE
      ══════════════════════════════════════════════════════════════════════ */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden space-y-4 p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-teal-700" />
              <h2 className="text-base font-bold text-slate-900">Source Registry &amp; Compliance Governance</h2>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Official insurance domains registered with strict permission status. Link-only sources are blocked from automated crawling.
            </p>
          </div>
          <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 self-start sm:self-auto">
            {sources.length} Registered Sources
          </span>
        </div>

        <div className="overflow-x-auto overflow-y-auto max-h-[380px]">
          <table className="w-full text-left text-xs min-w-[700px]">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 sticky top-0 z-10">
              <tr>
                <th className="p-3">Source Name &amp; Target URL</th>
                <th className="p-3">Type</th>
                <th className="p-3">Permission Status</th>
                <th className="p-3">Mode</th>
                <th className="p-3 text-right">Pipeline Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {sources.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="p-3 max-w-sm">
                    <div className="font-semibold text-slate-900">{s.source_name}</div>
                    <a
                      href={s.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] text-teal-700 hover:underline flex items-center gap-1 mt-0.5 truncate"
                    >
                      <span className="truncate">{s.source_url}</span>
                      <ExternalLink className="w-3 h-3 shrink-0" />
                    </a>
                  </td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-bold">{s.url_type}</span>
                  </td>
                  <td className="p-3">
                    {s.permission_status === 'permission_required' ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-bold">
                        <Lock className="w-3 h-3" /> Permission Required
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-bold">
                        <CheckCircle className="w-3 h-3" /> Authorized
                      </span>
                    )}
                  </td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      s.ingestion_mode === 'link_only'
                        ? 'bg-slate-100 text-slate-600 border border-slate-200'
                        : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    }`}>
                      {s.ingestion_mode.toUpperCase().replace('_', ' ')}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => handleTriggerSource(s.id, s.source_name)}
                      disabled={jobTriggering === s.id}
                      className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-[10px] font-semibold transition-colors disabled:opacity-50 inline-flex items-center gap-1 cursor-pointer"
                    >
                      <Play className="w-2.5 h-2.5" />
                      <span>{jobTriggering === s.id ? 'Checking...' : 'Test Ingestion'}</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          SECTION 3: INGESTION JOB TRACKER & AUDIT LOG
      ══════════════════════════════════════════════════════════════════════ */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden space-y-4 p-6 sm:p-8">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-700" />
            <h2 className="text-base font-bold text-slate-900">Ingestion Job Tracker &amp; Audit Log</h2>
          </div>
          <span className="text-xs text-slate-400">Idempotent background execution</span>
        </div>

        {jobs.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            No ingestion jobs recorded yet. Trigger a source or use the Market Watch to see live tracking.
          </div>
        ) : (
          <div className="overflow-x-auto overflow-y-auto max-h-[400px] rounded-xl border border-slate-200">
            <table className="w-full text-left text-xs min-w-[800px]">
              <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 sticky top-0 z-10">
                <tr>
                  <th className="p-3">Job ID &amp; Provider</th>
                  <th className="p-3">Job Type</th>
                  <th className="p-3">Target</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Authorization</th>
                  <th className="p-3">Records</th>
                  <th className="p-3">Completed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {jobs.map((j) => (
                  <tr key={j.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="p-3">
                      <div className="font-mono text-[10px] text-slate-400">{j.id.substring(0, 8)}...</div>
                      <div className="font-semibold text-slate-800" title={j.provider_slug}>
                        {formatProviderSlug(j.provider_slug)}
                      </div>
                      <div className="font-mono text-[10px] text-slate-400 mt-0.5">{j.provider_slug}</div>
                    </td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 text-[10px] font-bold border border-indigo-200">
                        {j.job_type}
                      </span>
                    </td>
                    <td className="p-3 max-w-xs truncate text-[11px] text-slate-600">
                      {j.requested_url || 'Registered Source'}
                    </td>
                    <td className="p-3"><JobStatusBadge status={j.status} /></td>
                    <td className="p-3">
                      <span className="text-[11px] font-mono text-slate-600">{j.authorization_decision}</span>
                      {j.failure_details && (
                        <p className="text-[10px] text-slate-400 mt-0.5 max-w-xs truncate">{j.failure_details}</p>
                      )}
                    </td>
                    <td className="p-3 font-semibold text-slate-800">
                      {j.created_record_count || 0} created / {j.updated_record_count || 0} updated
                    </td>
                    <td className="p-3 text-[11px] text-slate-500">
                      {j.completed_at ? new Date(j.completed_at).toLocaleTimeString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          SECTION 4: MANUAL INGESTION CHANNELS
      ══════════════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Channel 1: Manual PDF Upload */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-xs space-y-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-teal-50 text-teal-800 flex items-center justify-center">
              <Upload className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Upload Policy Wordings (PDF / TXT)</h2>
              <p className="text-xs text-slate-500">Extracts pages, headings, and indexes with SHA-256 integrity</p>
            </div>
          </div>

          {uploadSuccess && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-950 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-700 shrink-0" />
              <span>{uploadSuccess}</span>
            </div>
          )}
          {uploadError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-950 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-700 shrink-0" />
              <span>{uploadError}</span>
            </div>
          )}

          <form onSubmit={handleManualUpload} className="space-y-4 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Select Policy Document (.pdf, .txt)</label>
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => setUploadFile(e.target.files[0])}
                required
                className="w-full p-2 bg-slate-50 border border-slate-300 rounded-xl text-xs file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-teal-800 file:text-white hover:file:bg-teal-900 cursor-pointer"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Document Title (Optional)</label>
              <input
                type="text"
                placeholder="E.g. Star Health Senior Citizen Red Carpet 2026"
                value={docTitle}
                onChange={(e) => setDocTitle(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 placeholder-slate-400"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Insurer Name (Optional)</label>
              <input
                type="text"
                placeholder="E.g. Star Health and Allied Insurance"
                value={insurerName}
                onChange={(e) => setInsurerName(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 placeholder-slate-400"
              />
            </div>
            <button
              type="submit"
              disabled={uploading || !uploadFile}
              className="w-full py-2.5 px-4 bg-teal-800 hover:bg-teal-900 disabled:opacity-50 text-white rounded-xl font-semibold text-xs transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-xs"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>{uploading ? 'Parsing & Indexing Document...' : 'Upload & Process Document'}</span>
            </button>
          </form>
        </div>

        {/* Channel 2: Protected Web Scraper */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-xs space-y-5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center">
              <Globe className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Protected Web Disclosure Ingestion</h2>
              <p className="text-xs text-slate-500">SSRF-protected fetcher strictly checking authorization before network calls</p>
            </div>
          </div>

          {scrapeSuccess && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-950 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-700 shrink-0" />
              <span>{scrapeSuccess}</span>
            </div>
          )}
          {scrapeError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-950 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-700 shrink-0" />
              <span>{scrapeError}</span>
            </div>
          )}

          <form onSubmit={handleScrapeUrl} className="space-y-4 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Target Disclosure URL</label>
              <input
                type="url"
                placeholder="https://irdai.gov.in/health-insurance-products"
                value={scrapeUrl}
                onChange={(e) => setScrapeUrl(e.target.value)}
                required
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 placeholder-slate-400"
              />
              <span className="text-[10px] text-slate-400 mt-1 block">
                Protected by SSRF firewall (rejects loopback/metadata) and checks backend source permissions.
              </span>
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Source Title</label>
              <input
                type="text"
                placeholder="E.g. IRDAI Master Guidelines"
                value={scrapeTitle}
                onChange={(e) => setScrapeTitle(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 placeholder-slate-400"
              />
            </div>
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Insurer / Authority Name</label>
              <input
                type="text"
                placeholder="E.g. IRDAI"
                value={scrapeInsurer}
                onChange={(e) => setScrapeInsurer(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 placeholder-slate-400"
              />
            </div>
            <button
              type="submit"
              disabled={scraping || !scrapeUrl}
              className="w-full py-2.5 px-4 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white rounded-xl font-semibold text-xs transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-xs"
            >
              <Globe className="w-3.5 h-3.5" />
              <span>{scraping ? 'Validating Permissions & Fetching...' : 'Fetch & Ingest URL'}</span>
            </button>
          </form>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          SECTION 5: INDEXED DOCUMENT SOURCES & SHA-256 FINGERPRINTS
      ══════════════════════════════════════════════════════════════════════ */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <HardDrive className="w-4 h-4 text-teal-700" />
            <h3 className="font-bold text-slate-900 text-sm">Indexed Document Sources &amp; SHA-256 Fingerprints</h3>
          </div>
          <span className="text-xs text-slate-400">Tamper-evident Audit Trail</span>
        </div>

        <div className="overflow-x-auto overflow-y-auto max-h-[420px]">
          <table className="w-full text-left text-xs min-w-[800px]">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200 sticky top-0 z-10">
              <tr>
                <th className="p-3.5">Policy / Document Title</th>
                <th className="p-3.5">Type</th>
                <th className="p-3.5">Insurer / Authority</th>
                <th className="p-3.5">RAG Chunks</th>
                <th className="p-3.5">Status</th>
                <th className="p-3.5">SHA-256 Checksum</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {status?.recent_sources?.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50/60">
                  <td className="p-3.5 max-w-xs">
                    <div className="font-semibold text-slate-900 truncate">
                      {s.policy_name || s.title}
                    </div>
                    {s.policy_name && s.title && s.title !== s.policy_name && (
                      <div className="text-[11px] text-slate-400 truncate mt-0.5" title={s.title}>
                        {s.title}
                      </div>
                    )}
                  </td>
                  <td className="p-3.5">
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-bold">{s.source_type}</span>
                  </td>
                  <td className="p-3.5 text-slate-600">{s.insurer_name || 'General'}</td>
                  <td className="p-3.5 font-bold text-teal-800">{s.chunk_count} chunks</td>
                  <td className="p-3.5">
                    <span className="flex items-center gap-1 text-emerald-700 font-medium">
                      <CheckCircle className="w-3.5 h-3.5" /> Indexed
                    </span>
                  </td>
                  <td className="p-3.5 text-[10px] font-mono text-slate-400 max-w-xs">
                    {s.sha256_hash ? (
                      <span title={s.sha256_hash} className="cursor-help">
                        {s.sha256_hash.substring(0, 16)}&hellip;
                      </span>
                    ) : (
                      <span
                        title="No document binary available — policy sourced from IRDAI catalogue/regulatory filing, not a downloaded PDF"
                        className="cursor-help inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-100 text-slate-500 text-[10px] font-semibold border border-slate-200"
                      >
                        N/A
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
