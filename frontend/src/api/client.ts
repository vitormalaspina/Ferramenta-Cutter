import { AnalyzeResponse, JobConfig, JobProgress } from '../types';

const API_BASE = '/api';

const extractErrorMessage = async (res: Response): Promise<string> => {
  try {
    const text = await res.text();
    try {
      const data = JSON.parse(text);
      return data.detail || data.message || text || 'Erro desconhecido';
    } catch {
      return text || `Erro HTTP ${res.status}`;
    }
  } catch {
    return `Erro HTTP ${res.status}`;
  }
};

export const api = {
  analyze: async (url: string): Promise<AnalyzeResponse> => {
    const res = await fetch(`${API_BASE}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    if (!res.ok) throw new Error(await extractErrorMessage(res));
    return res.json();
  },

  getVideos: async (sourceId: string, page: number, search?: string, sort?: string): Promise<AnalyzeResponse> => {
    const params = new URLSearchParams({ page: page.toString() });
    if (search) params.append('search', search);
    if (sort) params.append('sort', sort);
    const res = await fetch(`${API_BASE}/videos/${sourceId}?${params.toString()}`);
    if (!res.ok) throw new Error(await extractErrorMessage(res));
    return res.json();
  },

  createJob: async (config: JobConfig): Promise<{ job_id: string }> => {
    const res = await fetch(`${API_BASE}/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    if (!res.ok) throw new Error(await extractErrorMessage(res));
    return res.json();
  },

  getJob: async (jobId: string): Promise<JobProgress> => {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (!res.ok) throw new Error(await extractErrorMessage(res));
    return res.json();
  },

  listJobs: async (): Promise<JobProgress[]> => {
    const res = await fetch(`${API_BASE}/jobs`);
    if (!res.ok) throw new Error(await extractErrorMessage(res));
    return res.json();
  },

  cancelJob: async (jobId: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(await extractErrorMessage(res));
  },

  generateZip: async (jobId: string): Promise<{ zip_path: string; zip_size_bytes: number }> => {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/zip`, { method: 'POST' });
    if (!res.ok) throw new Error(await extractErrorMessage(res));
    return res.json();
  },

  downloadZip: (jobId: string): void => {
    window.location.href = `${API_BASE}/jobs/${jobId}/download`;
  },

  deleteJobFiles: async (jobId: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/files`, { method: 'DELETE' });
    if (!res.ok) throw new Error(await extractErrorMessage(res));
  },

  getHealth: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(await extractErrorMessage(res));
    return res.json();
  },
};
