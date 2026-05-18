import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, CheckCircle, Terminal } from 'lucide-react';
import api from '../services/api';

export default function LiveResearchPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [logs, setLogs] = useState([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Initializing...');
  const logsEndRef = useRef(null);

  // Auto scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  useEffect(() => {
    // We use a raw EventSource pointing directly to the backend.
    // Ensure the backend URL is correct (using Vite's environment variable or hardcoded for now)
    const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001/api';
    const sseUrl = `${backendUrl}/research/${id}/stream`;
    
    console.log("Connecting to SSE:", sseUrl);
    const eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.status === 'LOG') {
          // It's a detailed workflow log
          setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), message: data.message }]);
        } else {
          // It's a major status update
          setStatus(data.status);
          setProgress(data.progress);
          setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), message: `>> System Status: ${data.status}` }]);
          
          if (data.status === 'JOB_FINISHED') {
            eventSource.close();
            // Wait a moment for UX, then redirect to report
            setTimeout(() => {
              navigate(`/report/${id}`);
            }, 1500);
          } else if (data.status === 'FAILED') {
            eventSource.close();
          }
        }
      } catch (err) {
        console.error("Error parsing SSE data", err);
      }
    };

    eventSource.onerror = (err) => {
      console.error("EventSource failed:", err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [id, navigate]);

  return (
    <div className="space-y-6 animate-fade-in max-w-4xl mx-auto pt-10">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-white mb-2">Autonomous Research in Progress</h1>
        <p className="text-white/50">CortexMCP is gathering, deduplicating, and analyzing data...</p>
      </div>

      <div className="glass p-8 space-y-8">
        {/* Progress Bar */}
        <div>
          <div className="flex justify-between items-end mb-2">
            <span className="text-lg font-medium text-primary-400 flex items-center gap-2">
              {status === 'JOB_FINISHED' ? (
                <CheckCircle className="w-5 h-5 text-emerald-400" />
              ) : status === 'FAILED' ? (
                <span className="text-red-400">FAILED</span>
              ) : (
                <Loader2 className="w-5 h-5 animate-spin" />
              )}
              {status}
            </span>
            <span className="text-white/60 font-mono">{progress}%</span>
          </div>
          <div className="w-full h-3 bg-white/5 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-primary-500 to-purple-500 transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Terminal Logs */}
        <div className="bg-slate-950/80 rounded-xl border border-white/5 p-4 font-mono text-sm shadow-inner">
          <div className="flex items-center gap-2 text-white/30 mb-4 pb-2 border-b border-white/5">
            <Terminal className="w-4 h-4" />
            <span>Worker Activity Log</span>
          </div>
          <div className="space-y-2 max-h-96 overflow-y-auto custom-scrollbar pr-2">
            {logs.map((log, i) => (
              <div key={i} className="flex gap-4 animate-fade-in">
                <span className="text-white/20 flex-shrink-0">{log.time}</span>
                <span className={log.message.startsWith('>>') ? 'text-primary-300 font-bold' : 'text-emerald-400/80'}>
                  {log.message}
                </span>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
}
