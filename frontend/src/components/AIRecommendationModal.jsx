import { useState, useEffect } from 'react';
import { API_BASE } from '../config';

export default function AIRecommendationModal({ isOpen, onClose, hotspotType, hotspotValue, stats }) {
  const [content, setContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!isOpen) { setContent(''); return; }
    setIsLoading(true);
    setContent('');

    const fetchRecommendations = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/ai/hotspot`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            hotspot_type: hotspotType,
            hotspot_value: hotspotValue,
            stats: stats || {},
          }),
        });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') continue;
              const decoded = data.replace(/\\n/g, '\n');
              setContent(prev => prev + decoded);
              setIsLoading(false);
            }
          }
        }
      } catch (err) {
        setContent('Could not connect to the AI backend. Make sure the server is running on port 8000.');
        setIsLoading(false);
      }
    };

    fetchRecommendations();
  }, [isOpen, hotspotType, hotspotValue, stats]);

  if (!isOpen) return null;

  // Format content: bold numbered items, bold **text**
  const formatContent = (text) => {
    return text.split('\n').map((line, i) => {
      // Bold **text** 
      const parts = line.split(/(\*\*.*?\*\*)/g);
      const formatted = parts.map((part, j) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={j} className="text-white">{part.slice(2, -2)}</strong>;
        }
        return part;
      });

      // Numbered list
      const isNumbered = /^\d+\./.test(line.trim());
      if (isNumbered) {
        return (
          <p key={i} className="mb-3 pl-1 leading-relaxed">
            {formatted}
          </p>
        );
      }
      return <p key={i} className="mb-2 leading-relaxed">{formatted}</p>;
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={onClose}>
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

      {/* Modal */}
      <div
        className="relative w-full max-w-2xl max-h-[80vh] mx-4 bg-dark-700 border border-dark-600 rounded-2xl shadow-2xl animate-fade-in overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-dark-600">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
              <h3 className="text-sm font-semibold text-white">AI Recommendations</h3>
            </div>
            <p className="text-xs text-gray-500">
              {hotspotType}: <span className="text-blue-400">{hotspotValue}</span>
            </p>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 transition-colors p-1 rounded-lg hover:bg-dark-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Stats badges */}
        {stats && (
          <div className="px-6 py-3 border-b border-dark-600 flex flex-wrap gap-2">
            {Object.entries(stats).map(([k, v]) => (
              <span key={k} className="text-[11px] px-2.5 py-1 rounded-full bg-dark-600 text-gray-400">
                {k.replace(/_/g, ' ')}: <span className="text-white font-medium">
                  {typeof v === 'number' ? (v >= 1000 ? `₹${(v/100000).toFixed(1)}L` : v.toFixed?.(4)?.replace(/\.?0+$/, '') || v) : v}
                </span>
              </span>
            ))}
          </div>
        )}

        {/* Body */}
        <div className="p-6 overflow-y-auto max-h-[55vh] text-sm text-gray-300">
          {isLoading ? (
            <div className="flex items-center justify-center py-10">
              <div className="flex gap-2">
                <span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '0ms' }} />
                <span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '200ms' }} />
                <span className="w-3 h-3 rounded-full bg-blue-500 pulse-dot" style={{ animationDelay: '400ms' }} />
              </div>
            </div>
          ) : (
            formatContent(content)
          )}
        </div>
      </div>
    </div>
  );
}
