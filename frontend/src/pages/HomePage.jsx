/**
 * Home page — research query submission with depth selector.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { researchAPI } from '../services/api';
import {
  Search, Sparkles, Zap, Shield, ArrowRight, AlertCircle,
  Brain, Globe, FileText, Layers
} from 'lucide-react';

const depthOptions = [
  {
    value: 'basic',
    label: 'Basic',
    description: '5 sources, quick overview',
    icon: Zap,
  },
  {
    value: 'standard',
    label: 'Standard',
    description: '10 sources, balanced depth',
    icon: Shield,
  },
  {
    value: 'deep',
    label: 'Deep',
    description: '20 sources, comprehensive',
    icon: Layers,
  },
];

const personaOptions = [
  {
    value: 'general',
    label: 'General Analyst',
    description: 'Standard balanced synthesis',
    icon: Sparkles,
  },
  {
    value: 'academic',
    label: 'Academic Reviewer',
    description: 'Scientific rigor & citations',
    icon: Brain,
  },
  {
    value: 'financial',
    label: 'Financial Auditor',
    description: 'SWOT, pricing & economics',
    icon: Layers,
  },
  {
    value: 'technical',
    label: 'Technical Architect',
    description: 'APIs, systems & RFC structure',
    icon: FileText,
  },
];

const features = [
  { icon: Globe, title: 'Web Search', desc: 'Autonomous multi-source research' },
  { icon: Brain, title: 'AI Summarization', desc: 'LLM-powered insight extraction' },
  { icon: Layers, title: 'Deduplication', desc: 'Semantic duplicate removal' },
  { icon: FileText, title: 'Report Generation', desc: 'Structured downloadable reports' },
];

export default function HomePage() {
  const [query, setQuery] = useState('');
  const [depth, setDepth] = useState('standard');
  const [persona, setPersona] = useState('general');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setError('');
    setLoading(true);

    try {
      const res = await researchAPI.start({ query: query.trim(), depth, persona });
      navigate(`/research/${res.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start research. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-12 animate-fade-in">
      {/* Hero */}
      <div className="text-center pt-8">
        <div className="inline-flex items-center gap-2 bg-primary-500/10 border border-primary-500/20 rounded-full px-4 py-1.5 mb-6">
          <Sparkles className="w-3.5 h-3.5 text-primary-400" />
          <span className="text-xs font-medium text-primary-300">AI-Powered Research Agent</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          <span className="gradient-text">Research Anything.</span>
          <br />
          <span className="text-white/90">Instantly.</span>
        </h1>
        <p className="text-lg text-white/40 max-w-2xl mx-auto">
          Enter a topic and let CortexMCP autonomously search, scrape, summarize, and generate comprehensive research reports.
        </p>
      </div>

      {/* Search Form */}
      <div className="max-w-3xl mx-auto">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-red-300 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          {/* Query Input */}
          <div className="glass p-2 glow-primary">
            <div className="relative">
              <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
              <input
                id="research-query"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full bg-transparent px-14 py-5 text-lg text-white placeholder-white/30 focus:outline-none"
                placeholder="Research latest advancements in autonomous AI agents..."
                minLength={3}
                required
              />
              <button
                id="research-submit"
                type="submit"
                disabled={loading || !query.trim()}
                className="absolute right-3 top-1/2 -translate-y-1/2 btn-primary flex items-center gap-2 text-sm py-2.5 px-5"
              >
                {loading ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    Research
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Depth Selector */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-white/40 uppercase tracking-wider pl-1">Research Depth</label>
            <div className="grid grid-cols-3 gap-3">
              {depthOptions.map(({ value, label, description, icon: Icon }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setDepth(value)}
                  className={`p-4 rounded-xl border text-left transition-all duration-200 ${
                    depth === value
                      ? 'bg-primary-500/10 border-primary-500/30 shadow-lg shadow-primary-500/5'
                      : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04] hover:border-white/[0.1]'
                  }`}
                >
                  <Icon className={`w-5 h-5 mb-2 ${depth === value ? 'text-primary-400' : 'text-white/30'}`} />
                  <p className={`text-sm font-semibold ${depth === value ? 'text-primary-300' : 'text-white/70'}`}>
                    {label}
                  </p>
                  <p className="text-xs text-white/30 mt-0.5">{description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Persona Selector */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-white/40 uppercase tracking-wider pl-1">Agent Research Profile</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {personaOptions.map(({ value, label, description, icon: Icon }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setPersona(value)}
                  className={`p-4 rounded-xl border text-left transition-all duration-200 ${
                    persona === value
                      ? 'bg-primary-500/10 border-primary-500/30 shadow-lg shadow-primary-500/5'
                      : 'bg-white/[0.02] border-white/[0.06] hover:bg-white/[0.04] hover:border-white/[0.1]'
                  }`}
                >
                  <Icon className={`w-5 h-5 mb-2 ${persona === value ? 'text-primary-400' : 'text-white/30'}`} />
                  <p className={`text-sm font-semibold ${persona === value ? 'text-primary-300' : 'text-white/70'}`}>
                    {label}
                  </p>
                  <p className="text-xs text-white/30 mt-0.5 leading-relaxed">{description}</p>
                </button>
              ))}
            </div>
          </div>
        </form>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4">
        {features.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="glass-card p-5 text-center">
            <div className="w-10 h-10 rounded-xl bg-primary-500/10 flex items-center justify-center mx-auto mb-3">
              <Icon className="w-5 h-5 text-primary-400" />
            </div>
            <h3 className="text-sm font-semibold text-white/80">{title}</h3>
            <p className="text-xs text-white/30 mt-1">{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
