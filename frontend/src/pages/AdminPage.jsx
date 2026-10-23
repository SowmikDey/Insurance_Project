import React, { useState, useEffect } from 'react';
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
  Play
} from 'lucide-react';

export const AdminPage = () => {
  const [status, setStatus] = useState(null);
  const [sources, setSources] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  // Manual Upload form
  const [uploadFile, setUploadFile] = useState(null);
  const [docTitle, setDocTitle] = useState('');
  const [insurerName, setInsurerName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  // Scraper form
  const [scrapeUrl, setScrapeUrl] = useState('');
  const [scrapeTitle, setScrapeTitle] = useState('');
  const [scrapeInsurer, setScrapeInsurer] = useState('');
  const [scraping, setScraping] = useState(false);
  const [scrapeSuccess, setScrapeSuccess] = useState(null);
  const [scrapeError, setScrapeError] = useState(null);

  // Job trigger feedback
  const [jobTriggering, setJobTriggering] = useState(null);
  const [actionNotice, setActionNotice] = useState(null);

  const fetchData = async () => {
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
  };

  useEffect(() => {
    fetchData();
  }, []);

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
      setUploadSuccess(`Document "${res.title}" successfully parsed and split into ${res.chunk_count} chunks with SHA-256 integrity verification!`);
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

  const handleScrapeUrl = async (e) => {
    e.preventDefault();
    if (!scrapeUrl) return;

    setScraping(true);
    setScrapeSuccess(null);
    setScrapeError(null);

    try {
      const res = await api.scrapeUrl(scrapeUrl, scrapeTitle || 'Web Disclosure', scrapeInsurer);
      setScrapeSuccess(`URL successfully scraped and indexed into ${res.chunk_count} RAG chunks!`);
      setScrapeUrl('');
      setScrapeTitle('');
      setScrapeInsurer('');
      fetchData();
    } catch (err) {
      setScrapeError(err.message || 'Scraping failed');
      fetchData(); // Refresh jobs to show the blocked status
    } finally {
      setScraping(false);
    }
  };

  const handleTriggerSource = async (sourceId, sourceName) => {
    setJobTriggering(sourceId);
    setActionNotice(null);
    try {
      const res = await api.runIngestionJob({ source_id: sourceId, job_type: 'FETCH_DOC' });
      if (res.status === 'BLOCKED_NO_PERMISSION') {
        setActionNotice({
          type: 'blocked',
          title: 'Ingestion Blocked by Authorization Policy',
          message: `Source "${sourceName}" is registered as "link_only". ${res.failure_details || 'Automated scraping is prohibited without written authorization.'}`
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
      setActionNotice({
        type: 'error',
        title: 'Execution Error',
        message: err.message
      });
      fetchData();
    } finally {
      setJobTriggering(null);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-800">
              Admin & Data Pipeline
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight mt-1">
            Data Ingestion & Source Governance
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Manage registered insurer sources, enforce authorization policies, upload policy wordings, and monitor pipeline jobs.
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-xl bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors self-start sm:self-auto cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Pipeline</span>
        </button>
      </div>

      {/* Action Notification Banner */}
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
          <div className="space-y-0.5">
            <h4 className="font-bold">{actionNotice.title}</h4>
            <p className="text-slate-600 leading-relaxed">{actionNotice.message}</p>
          </div>
        </div>
      )}

      {/* Overview Stats */}
      {status && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Indexed Sources</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-extrabold text-slate-900">{status.total_sources}</span>
              <span className="text-xs text-slate-500">PDFs / Disclosures</span>
            </div>
          </div>

          <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">RAG Document Chunks</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-extrabold text-teal-800">{status.total_chunks}</span>
              <span className="text-xs text-slate-500">Indexed Sections</span>
            </div>
          </div>

          <div className="p-5 bg-white rounded-2xl border border-slate-200 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Registered Sources</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-2xl font-extrabold text-indigo-700">{sources.length}</span>
              <span className="text-xs text-slate-500">Official URLs</span>
            </div>
          </div>
        </div>
      )}

      {/* Section 1: Registered Sources & Authorization Governance */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden space-y-4 p-6 sm:p-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-teal-700" />
              <h2 className="text-base font-bold text-slate-900">Source Registry & Compliance Governance</h2>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Official insurance domains registered with strict permission status. Link-only sources are blocked from automated web crawling.
            </p>
          </div>
          <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 self-start sm:self-auto">
            {sources.length} Registered Sources
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="p-3">Source Name & Target URL</th>
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
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-bold">
                      {s.url_type}
                    </span>
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

      {/* Section 2: Ingestion Job Tracker & Audit History */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden space-y-4 p-6 sm:p-8">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-700" />
            <h2 className="text-base font-bold text-slate-900">Ingestion Job Tracker & Audit Log</h2>
          </div>
          <span className="text-xs text-slate-400">Idempotent background execution</span>
        </div>

        {jobs.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            No ingestion jobs recorded yet. Trigger an authorized source or test a registered link to see live tracking.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
                <tr>
                  <th className="p-3">Job ID & Provider</th>
                  <th className="p-3">Requested Target</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Authorization Decision</th>
                  <th className="p-3">Extracted Chunks</th>
                  <th className="p-3">Completed At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {jobs.map((j) => (
                  <tr key={j.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="p-3">
                      <div className="font-mono text-[10px] text-slate-500">{j.id.substring(0, 8)}...</div>
                      <div className="font-semibold text-slate-800">{j.provider_slug}</div>
                    </td>
                    <td className="p-3 max-w-xs truncate text-[11px] text-slate-600">
                      {j.requested_url || 'Registered Source'}
                    </td>
                    <td className="p-3">
                      {j.status === 'BLOCKED_NO_PERMISSION' ? (
                        <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-200 text-[10px] font-bold">
                          BLOCKED (Link Only)
                        </span>
                      ) : j.status === 'COMPLETED' ? (
                        <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 text-[10px] font-bold">
                          COMPLETED
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-bold">
                          {j.status}
                        </span>
                      )}
                    </td>
                    <td className="p-3">
                      <span className="text-[11px] font-mono text-slate-600">
                        {j.authorization_decision}
                      </span>
                      {j.failure_details && (
                        <p className="text-[10px] text-slate-400 mt-0.5 max-w-xs truncate">{j.failure_details}</p>
                      )}
                    </td>
                    <td className="p-3 font-semibold text-slate-800">
                      {j.created_record_count || j.extracted_document_count} chunks
                    </td>
                    <td className="p-3 text-[11px] text-slate-500">
                      {j.completed_at ? new Date(j.completed_at).toLocaleTimeString() : 'In Progress'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Section 3: Ingestion Channels (Manual Upload vs Scraper) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Channel 1: Manual PDF Document Upload */}
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
                placeholder="E.g. Elevate Health Policy Wordings 2026"
                value={docTitle}
                onChange={(e) => setDocTitle(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 placeholder-slate-400"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Insurer Name (Optional)</label>
              <input
                type="text"
                placeholder="E.g. ICICI Lombard General Insurance"
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
                placeholder="https://policyholder.gov.in/guidelines"
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

      {/* Section 4: Recently Ingested Documents Table */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <HardDrive className="w-4 h-4 text-teal-700" />
            <h3 className="font-bold text-slate-900 text-sm">Indexed Document Sources & SHA-256 Fingerprints</h3>
          </div>
          <span className="text-xs text-slate-400">Tamper-evident Audit Trail</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-semibold border-b border-slate-200">
              <tr>
                <th className="p-3.5">Title</th>
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
                  <td className="p-3.5 font-medium text-slate-900 max-w-xs truncate">{s.title}</td>
                  <td className="p-3.5">
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-bold">
                      {s.source_type}
                    </span>
                  </td>
                  <td className="p-3.5 text-slate-600">{s.insurer_name || 'General'}</td>
                  <td className="p-3.5 font-bold text-teal-800">{s.chunk_count} chunks</td>
                  <td className="p-3.5">
                    <span className="flex items-center gap-1 text-emerald-700 font-medium">
                      <CheckCircle className="w-3.5 h-3.5" /> Indexed
                    </span>
                  </td>
                  <td className="p-3.5 text-[10px] font-mono text-slate-400 max-w-xs truncate">
                    {s.sha256_hash ? `${s.sha256_hash.substring(0, 16)}...` : 'N/A'}
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
