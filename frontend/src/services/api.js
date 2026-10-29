const API_BASE = '/api/v1';

async function handleResponse(res) {
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Policies & Categories
  getCategories: async () => {
    const res = await fetch(`${API_BASE}/policies/categories`);
    return handleResponse(res);
  },

  getInsurers: async () => {
    const res = await fetch(`${API_BASE}/policies/insurers`);
    return handleResponse(res);
  },

  getPolicies: async (params = {}) => {
    const searchParams = new URLSearchParams();
    if (params.category && params.category !== 'all') searchParams.set('category', params.category);
    if (params.insurer && params.insurer !== 'all') searchParams.set('insurer', params.insurer);
    if (params.min_sum_insured) searchParams.set('min_sum_insured', params.min_sum_insured);
    if (params.max_budget) searchParams.set('max_budget', params.max_budget);
    if (params.zero_copay) searchParams.set('zero_copay', 'true');
    if (params.no_room_rent_capping) searchParams.set('no_room_rent_capping', 'true');
    if (params.search) searchParams.set('search', params.search);
    if (params.sort_by) searchParams.set('sort_by', params.sort_by);
    if (params.page) searchParams.set('page', params.page);
    if (params.page_size) searchParams.set('page_size', params.page_size);

    const res = await fetch(`${API_BASE}/policies?${searchParams.toString()}`);
    return handleResponse(res);
  },

  getPolicyDetail: async (slugOrId) => {
    const res = await fetch(`${API_BASE}/policies/${slugOrId}`);
    return handleResponse(res);
  },

  // Glossary
  getGlossaryTerms: async (category = null) => {
    const url = category && category !== 'all' 
      ? `${API_BASE}/glossary?category=${encodeURIComponent(category)}`
      : `${API_BASE}/glossary`;
    const res = await fetch(url);
    return handleResponse(res);
  },

  getGlossaryTerm: async (slug) => {
    const res = await fetch(`${API_BASE}/glossary/${slug}`);
    return handleResponse(res);
  },

  detectGlossaryTerms: async (text) => {
    const res = await fetch(`${API_BASE}/glossary/detect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    return handleResponse(res);
  },

  // Education
  getModules: async () => {
    const res = await fetch(`${API_BASE}/education/modules`);
    return handleResponse(res);
  },

  getModuleDetail: async (slug) => {
    const res = await fetch(`${API_BASE}/education/modules/${slug}`);
    return handleResponse(res);
  },

  submitQuiz: async (answers) => {
    const res = await fetch(`${API_BASE}/education/quiz/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers })
    });
    return handleResponse(res);
  },

  // AI Assistant (RAG)
  chatAssistant: async (query, history = [], policyId = null) => {
    const res = await fetch(`${API_BASE}/assistant/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        history: history,
        policy_id: policyId
      })
    });
    return handleResponse(res);
  },

  chatAssistantWithDocument: async (file, query, history = []) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('query', query);
    formData.append('history', JSON.stringify(history));

    const res = await fetch(`${API_BASE}/assistant/chat-document`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(res);
  },


  // Ingestion & Admin
  getIngestionStatus: async () => {
    const res = await fetch(`${API_BASE}/ingestion/status`);
    return handleResponse(res);
  },

  getSourceRegistries: async (provider = null) => {
    const url = provider ? `${API_BASE}/ingestion/sources?provider=${encodeURIComponent(provider)}` : `${API_BASE}/ingestion/sources`;
    const res = await fetch(url);
    return handleResponse(res);
  },

  getSourceAuthorizations: async () => {
    const res = await fetch(`${API_BASE}/ingestion/authorizations`);
    return handleResponse(res);
  },

  getIngestionJobs: async (limit = 20) => {
    const res = await fetch(`${API_BASE}/ingestion/jobs?limit=${limit}`);
    return handleResponse(res);
  },

  getPolicyFacts: async (policyId) => {
    const res = await fetch(`${API_BASE}/ingestion/facts/${policyId}`);
    return handleResponse(res);
  },

  runIngestionJob: async (payload) => {
    const res = await fetch(`${API_BASE}/ingestion/jobs/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    return handleResponse(res);
  },

  uploadDocument: async (formData) => {
    const adminKey = localStorage.getItem('bimagyan_admin_key') || 'bimagyan-admin-secret-2026';
    const res = await fetch(`${API_BASE}/ingestion/upload`, {
      method: 'POST',
      headers: {
        'X-Admin-API-Key': adminKey
      },
      body: formData
    });
    return handleResponse(res);
  },

  scrapeUrl: async (url, title, insurerName = null) => {
    const res = await fetch(`${API_BASE}/ingestion/scrape`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: url,
        title: title,
        insurer_name: insurerName
      })
    });
    return handleResponse(res);
  },

  // Market Watch & Policy Lifecycle Governance
  getMarketUpdates: async () => {
    const res = await fetch(`${API_BASE}/ingestion/market-updates`);
    return handleResponse(res);
  },

  scanMarketUpdates: async () => {
    const res = await fetch(`${API_BASE}/ingestion/market-updates/scan`, {
      method: 'POST'
    });
    return handleResponse(res);
  },

  applyMarketUpdates: async (items, appliedBy = 'Admin') => {
    const res = await fetch(`${API_BASE}/ingestion/market-updates/apply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items, applied_by: appliedBy })
    });
    return handleResponse(res);
  },

  updatePolicyStatus: async (policyId, status, reason = null) => {
    const res = await fetch(`${API_BASE}/ingestion/policies/${policyId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, reason })
    });
    return handleResponse(res);
  },

  // Model Retraining & Cloudflare Edge Pipeline
  getRetrainStatus: async () => {
    const res = await fetch(`${API_BASE}/retrain/status`);
    return handleResponse(res);
  },

  triggerRetrainPipeline: async () => {
    const res = await fetch(`${API_BASE}/retrain/trigger`, {
      method: 'POST'
    });
    return handleResponse(res);
  },

  updateRetrainConfig: async (config) => {
    const res = await fetch(`${API_BASE}/retrain/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    return handleResponse(res);
  }
};
