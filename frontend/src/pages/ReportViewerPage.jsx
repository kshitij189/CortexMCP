import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, FileText, Download } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import api from '../services/api';

export default function ReportViewerPage() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchReport();
    
    // Poll if not finished
    const interval = setInterval(() => {
      if (job && job.job.status !== 'JOB_FINISHED' && job.job.status !== 'FAILED') {
        fetchReport();
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [id, job?.job?.status]);

  const fetchReport = async () => {
    try {
      const response = await api.get(`/research/${id}`);
      setJob(response.data);
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const response = await api.get(`/research/${id}/pdf`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `CortexMCP_Report_${id.substring(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Failed to download PDF. Please try again.');
    }
  };

  const handleDownloadDocx = async () => {
    try {
      const response = await api.get(`/research/${id}/docx`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `CortexMCP_Report_${id.substring(0, 8)}.docx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert('Failed to download DOCX. Please try again.');
    }
  };

  if (loading && !job) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-white/40">Loading research job...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center min-h-[50vh] flex flex-col items-center justify-center space-y-4">
        <p className="text-red-400">{error}</p>
        <Link to="/dashboard" className="text-primary-400 hover:text-primary-300">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const isFinished = job?.job?.status === 'JOB_FINISHED';
  const hasReport = !!job?.report;

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="space-y-2">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 text-sm text-white/40 hover:text-white/70 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>
          <h1 className="text-2xl font-semibold text-white">
            {job.job.query}
          </h1>
          <div className="flex items-center gap-2 text-sm">
            <span className={`px-2 py-0.5 rounded-full ${isFinished ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'}`}>
              {job.job.status}
            </span>
            <span className="text-white/40">{job.job.progress}% Complete</span>
          </div>
        </div>

        {isFinished && hasReport && (
          <div className="flex gap-2">
            <button
              onClick={handleDownloadPDF}
              className="btn-primary inline-flex items-center gap-2 text-sm py-2.5 px-4"
            >
              <Download className="w-4 h-4" />
              Export PDF
            </button>
            <button
              onClick={handleDownloadDocx}
              className="bg-white/[0.06] hover:bg-white/[0.1] text-white border border-white/[0.1] rounded-xl font-medium inline-flex items-center gap-2 text-sm py-2.5 px-4 transition-all"
            >
              <Download className="w-4 h-4" />
              Download DOCX
            </button>
          </div>
        )}
      </div>

      {!isFinished && job?.job?.status !== 'FAILED' && (
        <div className="glass p-12 text-center flex flex-col items-center justify-center space-y-4">
          <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mb-2" />
          <h3 className="text-xl font-medium text-white">Agents are Working</h3>
          <p className="text-white/40 max-w-md">
            Your research job is currently being processed by the background agents. 
            They are searching, scraping, deduplicating, and summarizing the web.
          </p>
        </div>
      )}
      
      {job?.job?.status === 'FAILED' && (
        <div className="glass p-12 text-center flex flex-col items-center justify-center space-y-4">
          <h3 className="text-xl font-medium text-red-400">Research Failed</h3>
          <p className="text-white/60 max-w-md">{job.job.error_message || "An unknown error occurred during the pipeline."}</p>
        </div>
      )}

      {isFinished && hasReport && (
        <div className="glass p-8 lg:p-12 overflow-hidden">
          <article className="prose prose-invert prose-primary max-w-none">
            <ReactMarkdown>{job.report.report_markdown}</ReactMarkdown>
          </article>
        </div>
      )}

      {isFinished && !hasReport && (
        <div className="glass p-12 text-center text-amber-400">
          <p>The job finished, but no report was generated.</p>
        </div>
      )}
    </div>
  );
}
