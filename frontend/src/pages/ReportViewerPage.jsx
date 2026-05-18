import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, FileText, Download, Share2,
  RefreshCw, GitCompare, History, X, Sparkles,
  Clock, CheckCircle2, ChevronRight
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import api, { researchAPI } from '../services/api';

const getDomain = (url) => {
  try {
    return new URL(url).hostname.replace('www.', '');
  } catch (e) {
    return url;
  }
};

const hasMatchingLink = (children, domain) => {
  if (!domain) return false;
  let found = false;
  const check = (node) => {
    if (!node) return;
    if (typeof node === 'object') {
      if (node.type === 'a' && node.props?.href?.toLowerCase().includes(domain.toLowerCase())) {
        found = true;
      }
      if (node.props?.children) {
        if (Array.isArray(node.props.children)) {
          node.props.children.forEach(check);
        } else {
          check(node.props.children);
        }
      }
    }
  };
  if (Array.isArray(children)) {
    children.forEach(check);
  } else {
    check(children);
  }
  return found;
};

export default function ReportViewerPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [selectedSource, setSelectedSource] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Temporal Delta Tracking states
  const [compareMode, setCompareMode] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareError, setCompareError] = useState('');
  const [showDeltaDrawer, setShowDeltaDrawer] = useState(true);
  const [updating, setUpdating] = useState(false);

  const handleToggleCompare = async () => {
    if (compareMode) {
      setCompareMode(false);
      return;
    }

    if (comparisonData) {
      setCompareMode(true);
      return;
    }

    setCompareLoading(true);
    setCompareError('');
    try {
      const response = await researchAPI.getComparison(id);
      setComparisonData(response.data);
      setCompareMode(true);
    } catch (err) {
      setCompareError(err.response?.data?.detail || 'Failed to generate comparison analysis');
    } finally {
      setCompareLoading(false);
    }
  };

  const handleUpdateResearch = async () => {
    if (updating) return;
    setUpdating(true);
    try {
      const res = await researchAPI.start({
        query: job.job.query,
        depth: job.job.depth,
        persona: job.job.persona || 'general',
        parent_job_id: id
      });
      navigate(`/research/${res.data.id}`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to start research update');
    } finally {
      setUpdating(false);
    }
  };

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

  if (compareMode && comparisonData) {
    return (
      <div className="space-y-6 animate-fade-in max-w-[95vw] mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-white/[0.06] pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs text-white/40">
              <History className="w-3.5 h-3.5" />
              <span>Temporal Delta Tracking</span>
            </div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <GitCompare className="w-6 h-6 text-primary-400" />
              Comparing: {comparisonData.query}
            </h1>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowDeltaDrawer(true)}
              className="btn-primary inline-flex items-center gap-2 text-sm py-2.5 px-4 bg-primary-600 hover:bg-primary-500"
            >
              <Sparkles className="w-4 h-4" />
              View AI Delta Report
            </button>
            <button
              onClick={() => setCompareMode(false)}
              className="bg-white/[0.06] hover:bg-white/[0.1] text-white border border-white/[0.1] rounded-xl font-medium inline-flex items-center gap-2 text-sm py-2.5 px-4 transition-all"
            >
              Back to Latest Report
            </button>
          </div>
        </div>

        {/* Split Screen Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[65vh]">
          {/* Left Pane - Previous Version */}
          <div className="glass p-6 md:p-8 flex flex-col h-[70vh]">
            <div className="flex justify-between items-center mb-4 border-b border-white/[0.06] pb-3">
              <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider flex items-center gap-2">
                <Clock className="w-4 h-4 text-white/40" />
                Previous Version
              </h3>
              <span className="text-xs text-white/30">ID: {comparisonData.parent_job_id.substring(0, 8)}</span>
            </div>
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
              <article className="prose prose-invert prose-primary max-w-none prose-sm">
                <ReactMarkdown>{comparisonData.parent_report}</ReactMarkdown>
              </article>
            </div>
          </div>

          {/* Right Pane - Latest Version */}
          <div className="glass p-6 md:p-8 flex flex-col h-[70vh] border-primary-500/20 relative shadow-[0_0_50px_-12px_rgba(168,85,247,0.15)]">
            <div className="absolute -top-3 left-6 px-3 py-1 rounded-full bg-primary-500/10 border border-primary-500/20 text-[10px] font-semibold text-primary-300 uppercase tracking-widest">
              LATEST ITERATION
            </div>
            <div className="flex justify-between items-center mb-4 border-b border-white/[0.06] pb-3">
              <h3 className="text-sm font-semibold text-primary-300 uppercase tracking-wider flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Updated Version
              </h3>
              <span className="text-xs text-white/30">ID: {comparisonData.child_job_id.substring(0, 8)}</span>
            </div>
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
              <article className="prose prose-invert prose-primary max-w-none prose-sm">
                <ReactMarkdown>{comparisonData.child_report}</ReactMarkdown>
              </article>
            </div>
          </div>
        </div>

        {/* AI Delta Slide-out Drawer */}
        {showDeltaDrawer && (
          <div className="fixed inset-0 z-50 overflow-hidden" aria-labelledby="slide-over-title" role="dialog" aria-modal="true">
            <div className="absolute inset-0 overflow-hidden">
              {/* Backdrop */}
              <div 
                className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity" 
                onClick={() => setShowDeltaDrawer(false)}
              />

              <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
                <div className="pointer-events-auto w-screen max-w-xl transform transition-transform duration-500 ease-in-out">
                  <div className="flex h-full flex-col overflow-y-scroll bg-black/90 border-l border-white/[0.08] backdrop-blur-2xl shadow-2xl p-6 relative">
                    <div className="flex items-center justify-between border-b border-white/[0.08] pb-4 mb-4">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-primary-400" />
                        <h2 className="text-lg font-bold text-white" id="slide-over-title">
                          AI Temporal Delta Analysis
                        </h2>
                      </div>
                      <button
                        onClick={() => setShowDeltaDrawer(false)}
                        className="rounded-lg p-1.5 text-white/40 hover:text-white/80 hover:bg-white/[0.06] transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>

                    <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                      <article className="prose prose-invert prose-primary max-w-none text-sm leading-relaxed">
                        <ReactMarkdown>{comparisonData.delta_report}</ReactMarkdown>
                      </article>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto">
      {compareError && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-300 rounded-xl p-4 text-sm flex items-center justify-between animate-fade-in">
          <span>{compareError}</span>
          <button onClick={() => setCompareError('')} className="text-red-300/60 hover:text-red-300">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
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
          <div className="flex flex-wrap gap-2">
            {job.job.parent_job_id && (
              <button
                onClick={handleToggleCompare}
                disabled={compareLoading}
                className="bg-primary-500/10 hover:bg-primary-500/20 text-primary-300 border border-primary-500/30 rounded-xl font-medium inline-flex items-center gap-2 text-sm py-2.5 px-4 transition-all disabled:opacity-50"
              >
                {compareLoading ? (
                  <div className="w-4 h-4 border-2 border-primary-300 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <GitCompare className="w-4 h-4" />
                )}
                Compare Versions
              </button>
            )}
            
            <button
              onClick={handleUpdateResearch}
              disabled={updating}
              className="bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 rounded-xl font-medium inline-flex items-center gap-2 text-sm py-2.5 px-4 transition-all disabled:opacity-50"
            >
              {updating ? (
                <div className="w-4 h-4 border-2 border-emerald-300 border-t-transparent rounded-full animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              Update Research
            </button>

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
        <div className="space-y-6">
          {/* Interactive Source Citation Network */}
          <div className="glass p-6 glow-primary">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Share2 className="w-5 h-5 text-primary-400" />
                  Interactive Source Citation Network
                </h2>
                <p className="text-xs text-white/40 mt-1">
                  Click on any website node to audit references and highlight matching evidence in the report below.
                </p>
              </div>
              {selectedSource && (
                <button
                  onClick={() => setSelectedSource(null)}
                  className="text-xs text-primary-400 hover:text-primary-300 font-medium transition-colors"
                >
                  Clear Selection
                </button>
              )}
            </div>
            
            <SourceCitationGraph
              query={job.job.query}
              sources={job.sources}
              selectedSource={selectedSource}
              onSelectSource={setSelectedSource}
            />
          </div>

          {/* Sourced Evidence & Report Body */}
          <div className="glass p-8 lg:p-12 overflow-hidden">
            <article className="prose prose-invert prose-primary max-w-none">
              <ReactMarkdown
                components={{
                  a: ({ href, children }) => {
                    const isHighlighted = selectedSource && href && href.toLowerCase().includes(getDomain(selectedSource.url).toLowerCase());
                    return (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`transition-all duration-300 font-semibold ${
                          isHighlighted
                            ? 'bg-primary-500/20 text-primary-300 ring-2 ring-primary-500/50 rounded px-1.5 py-0.5'
                            : 'text-primary-400 hover:text-primary-300'
                        }`}
                      >
                        {children}
                      </a>
                    );
                  },
                  p: ({ children }) => {
                    const isHighlighted = selectedSource && hasMatchingLink(children, getDomain(selectedSource.url));
                    return (
                      <p
                        className={`transition-all duration-300 border-l-2 pl-3 ${
                          isHighlighted
                            ? 'border-primary-500 bg-primary-500/5 py-2 rounded-r-lg shadow-sm shadow-primary-500/5'
                            : 'border-transparent'
                        }`}
                      >
                        {children}
                      </p>
                    );
                  },
                  li: ({ children }) => {
                    const isHighlighted = selectedSource && hasMatchingLink(children, getDomain(selectedSource.url));
                    return (
                      <li
                        className={`transition-all duration-300 border-l-2 pl-3 list-none ${
                          isHighlighted
                            ? 'border-primary-500 bg-primary-500/5 py-1 rounded-r-lg shadow-sm shadow-primary-500/5'
                            : 'border-transparent'
                        }`}
                      >
                        • {children}
                      </li>
                    );
                  }
                }}
              >
                {job.report.report_markdown}
              </ReactMarkdown>
            </article>
          </div>
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

function SourceCitationGraph({ query, sources, selectedSource, onSelectSource }) {
  const [hoveredNode, setHoveredNode] = useState(null);
  
  if (!sources || sources.length === 0) return null;
  
  const width = 800;
  const height = 400;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 130;
  
  // Arrange nodes in an orbital ring
  const nodes = sources.map((src, idx) => {
    const angle = (idx * 2 * Math.PI) / sources.length;
    return {
      ...src,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      domain: getDomain(src.url),
    };
  });
  
  return (
    <div className="space-y-4">
      {/* SVG Canvas */}
      <div className="relative bg-black/30 border border-white/[0.04] rounded-2xl overflow-hidden aspect-[2/1] w-full max-h-[400px]">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full select-none">
          {/* Connector Lines */}
          {nodes.map((node) => {
            const isSelected = selectedSource?.id === node.id;
            const isHovered = hoveredNode?.id === node.id;
            return (
              <line
                key={`line-${node.id}`}
                x1={centerX}
                y1={centerY}
                x2={node.x}
                y2={node.y}
                className={`transition-all duration-300 ${
                  isSelected
                    ? 'stroke-primary-500 stroke-[3px] opacity-100'
                    : isHovered
                    ? 'stroke-primary-400 stroke-[2px] opacity-80'
                    : 'stroke-white/10 stroke-[1px] opacity-40'
                }`}
                strokeDasharray={isSelected ? '5,5' : 'none'}
              />
            );
          })}
          
          {/* Central Query Node */}
          <g className="cursor-pointer">
            <circle
              cx={centerX}
              cy={centerY}
              r={36}
              className="fill-primary-950/80 stroke-primary-500 stroke-2 filter drop-shadow-[0_0_12px_rgba(168,85,247,0.4)] transition-all duration-300"
            />
            {/* Pulsing Outer Ring */}
            <circle
              cx={centerX}
              cy={centerY}
              r={44}
              className="fill-transparent stroke-primary-500/30 stroke-1 animate-pulse"
            />
            <text
              x={centerX}
              y={centerY + 4}
              textAnchor="middle"
              className="fill-primary-300 text-[10px] font-semibold tracking-wider uppercase pointer-events-none"
            >
              QUERY
            </text>
          </g>
          
          {/* Surrounding Source Nodes */}
          {nodes.map((node) => {
            const isSelected = selectedSource?.id === node.id;
            const isHovered = hoveredNode?.id === node.id;
            const size = isSelected ? 22 : isHovered ? 18 : 14;
            
            return (
              <g
                key={node.id}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredNode(node)}
                onMouseLeave={() => setHoveredNode(null)}
                onClick={() => {
                  onSelectSource(isSelected ? null : node);
                  // Smoothly scroll to first highlighted element in report
                  setTimeout(() => {
                    const firstHighlight = document.querySelector('.border-primary-500');
                    if (firstHighlight) {
                      firstHighlight.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                  }, 100);
                }}
              >
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={size}
                  className={`transition-all duration-300 ${
                    isSelected
                      ? 'fill-primary-500 stroke-white stroke-2'
                      : isHovered
                      ? 'fill-primary-400 stroke-primary-300 stroke-1'
                      : node.relevance_score > 0.8
                      ? 'fill-emerald-500/80 stroke-emerald-400/50 stroke-1'
                      : 'fill-sky-500/80 stroke-sky-400/50 stroke-1'
                  }`}
                />
                
                {/* Clean Domain Label Text */}
                <text
                  x={node.x}
                  y={node.y + size + 16}
                  textAnchor="middle"
                  className={`text-[9px] font-medium transition-colors duration-300 pointer-events-none ${
                    isSelected || isHovered
                      ? 'fill-primary-300 font-semibold'
                      : 'fill-white/40'
                  }`}
                >
                  {node.domain.length > 20 ? node.domain.substring(0, 17) + '...' : node.domain}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
      
      {/* Dynamic Detail Card */}
      {(selectedSource || hoveredNode) && (
        <div className="glass p-4 rounded-xl border border-primary-500/20 bg-primary-500/[0.02] animate-fade-in">
          <div className="flex justify-between items-start gap-4">
            <div className="space-y-1">
              <span className="text-[10px] uppercase tracking-wider font-semibold text-primary-400">
                {selectedSource ? 'Selected Reference' : 'Hovered Source'}
              </span>
              <h4 className="text-sm font-semibold text-white">
                {(selectedSource || hoveredNode).title || 'Untitled Source'}
              </h4>
              <a
                href={(selectedSource || hoveredNode).url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-primary-300 hover:underline inline-flex items-center gap-1"
              >
                {(selectedSource || hoveredNode).url}
              </a>
              <p className="text-xs text-white/50 leading-relaxed mt-2">
                {(selectedSource || hoveredNode).summary || 'No summary extracted for this source.'}
              </p>
            </div>
            <div className="text-right flex-shrink-0">
              <span className="text-[10px] text-white/30 block">RELEVANCE</span>
              <span className="text-lg font-bold text-emerald-400">
                {Math.round(((selectedSource || hoveredNode).relevance_score || 0.8) * 100)}%
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
