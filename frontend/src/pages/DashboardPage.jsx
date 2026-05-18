/**
 * Dashboard page — research history with search, filter, sort.
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { researchAPI } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import { formatRelativeTime } from '../utils/formatters';
import {
  Search, Filter, Trash2, ExternalLink, RefreshCw,
  Clock, AlertCircle, Inbox
} from 'lucide-react';

const statusTabs = [
  { value: null, label: 'All' },
  { value: 'JOB_CREATED', label: 'Created' },
  { value: 'running', label: 'Running' },
  { value: 'JOB_FINISHED', label: 'Completed' },
  { value: 'FAILED', label: 'Failed' },
];

// Running statuses for filter
const RUNNING_STATUSES = [
  'SEARCHING', 'SCRAPING', 'SUMMARIZING',
  'SEARCH_STARTED', 'SEARCH_COMPLETED', 'SCRAPING_STARTED', 'SCRAPING_COMPLETED',
  'SUMMARIZATION_STARTED', 'SUMMARIZATION_COMPLETED', 'DEDUPLICATION_STARTED',
  'DEDUPLICATION_COMPLETED', 'REPORT_GENERATION_STARTED', 'REPORT_GENERATION_COMPLETED',
];

export default function DashboardPage() {
  const [jobs, setJobs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = { limit: 50, offset: 0 };
      // For specific status filter (not 'running' group)
      if (activeTab && activeTab !== 'running') {
        params.status = activeTab;
      }
      const res = await researchAPI.listJobs(params);
      let filtered = res.data.jobs;

      // Client-side filter for 'running' group
      if (activeTab === 'running') {
        filtered = filtered.filter(j => RUNNING_STATUSES.includes(j.status));
      }

      // Client-side search filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        filtered = filtered.filter(j => j.query.toLowerCase().includes(q));
      }

      setJobs(filtered);
      setTotal(res.data.total);
    } catch (err) {
      setError('Failed to load research jobs');
    } finally {
      setLoading(false);
    }
  }, [activeTab, searchQuery]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const handleDelete = async (e, jobId) => {
    e.stopPropagation();
    if (!confirm('Delete this research job?')) return;
    try {
      await researchAPI.deleteJob(jobId);
      fetchJobs();
    } catch {
      setError('Failed to delete job');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Research Dashboard</h1>
          <p className="text-white/40 text-sm mt-1">{total} total research jobs</p>
        </div>
        <button onClick={fetchJobs} className="btn-secondary flex items-center gap-2 text-sm py-2 px-4">
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Search + Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
          <input
            id="dashboard-search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="glass-input w-full pl-11 py-2.5 text-sm"
            placeholder="Search research queries..."
          />
        </div>
      </div>

      {/* Status Tabs */}
      <div className="flex gap-2 border-b border-white/[0.06] pb-1">
        {statusTabs.map(({ value, label }) => (
          <button
            key={label}
            onClick={() => setActiveTab(value)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
              activeTab === value
                ? 'bg-primary-500/15 text-primary-300'
                : 'text-white/40 hover:text-white/60 hover:bg-white/[0.04]'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-red-300 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Job List */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-20">
          <Inbox className="w-12 h-12 text-white/10 mx-auto mb-4" />
          <p className="text-white/30 text-lg">No research jobs found</p>
          <p className="text-white/20 text-sm mt-1">Start a new research from the Home page</p>
        </div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <div
              key={job.id}
              onClick={() => navigate(job.status === 'JOB_FINISHED' ? `/report/${job.id}` : `/research/${job.id}`)}
              className="glass-card p-5 cursor-pointer group"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <StatusBadge status={job.status} />
                    <span className="text-xs text-white/20 uppercase tracking-wider">{job.depth}</span>
                  </div>
                  <h3 className="text-white/90 font-medium truncate group-hover:text-primary-300 transition-colors">
                    {job.query}
                  </h3>
                  <div className="flex items-center gap-4 mt-2">
                    <span className="flex items-center gap-1.5 text-xs text-white/30">
                      <Clock className="w-3 h-3" />
                      {formatRelativeTime(job.created_at)}
                    </span>
                    {job.progress > 0 && (
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-primary-500 to-purple-500 rounded-full transition-all duration-500"
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-white/30">{job.progress}%</span>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => handleDelete(e, job.id)}
                    className="p-2 rounded-lg hover:bg-red-500/10 text-white/30 hover:text-red-400 transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <ExternalLink className="w-4 h-4 text-white/20" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
