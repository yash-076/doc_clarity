import React, { useState } from 'react';
import { X, Search, Loader2, Sparkles, Tag, CheckCircle2, AlertCircle } from 'lucide-react';
import { documentApi } from '../services/documentApi';

export default function DocumentSearchModal({ document, onClose }) {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [searching, setSearching] = useState(false);
  const [resultsData, setResultsData] = useState(null);
  const [error, setError] = useState(null);

  if (!document) return null;

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setSearching(true);
    setError(null);

    try {
      const data = await documentApi.searchDocument(document.id, query.trim(), topK);
      setResultsData(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Vector retrieval search failed.");
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="glass-card rounded-2xl w-full max-w-4xl h-[85vh] flex flex-col overflow-hidden border border-slate-700/80 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-900/60 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
              <Search className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                Semantic Vector Search
                <span className="text-xs font-semibold px-2.5 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Document Isolated
                </span>
              </h3>
              <p className="text-xs text-slate-400 truncate max-w-md mt-0.5">
                Target: <span className="text-slate-200 font-semibold">{document.original_filename}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search Bar Input Form */}
        <div className="p-6 bg-slate-900/40 border-b border-slate-800 shrink-0 space-y-4">
          <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a natural language query e.g. What conditions are excluded?"
                className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <div className="flex items-center gap-2 bg-slate-950/80 border border-slate-700/80 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400">
                <span>Top K:</span>
                <select
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                  className="bg-transparent text-indigo-400 font-bold focus:outline-none cursor-pointer"
                >
                  <option value={3}>3</option>
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={15}>15</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={!query.trim() || searching}
                className={`py-2.5 px-6 rounded-xl font-semibold text-sm transition-all duration-200 flex items-center gap-2 ${
                  !query.trim() || searching
                    ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                    : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/30'
                }`}
              >
                {searching ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Searching...
                  </>
                ) : (
                  'Search Chunks'
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Results Container */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {searching && (
            <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
              <p className="text-sm font-medium">Generating query embedding & querying ChromaDB vectors...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          )}

          {!searching && !resultsData && !error && (
            <div className="py-20 text-center text-slate-500 text-sm flex flex-col items-center justify-center space-y-2">
              <Sparkles className="w-8 h-8 text-slate-600" />
              <p>Type a semantic search query above to test ChromaDB retrieval scores.</p>
            </div>
          )}

          {!searching && resultsData && resultsData.results.length === 0 && (
            <div className="py-16 text-center text-slate-400 text-sm">
              No matching chunks found for this document.
            </div>
          )}

          {!searching && resultsData && resultsData.results.map((res, index) => {
            const pct = Math.round(res.score * 100);
            return (
              <div
                key={res.chunk_id}
                className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-3 hover:border-indigo-500/40 transition-colors"
              >
                {/* Result Item Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-400 text-xs font-bold flex items-center justify-center">
                      #{index + 1}
                    </span>
                    {res.section && (
                      <span className="text-xs font-semibold text-slate-300 flex items-center gap-1">
                        <Tag className="w-3.5 h-3.5 text-indigo-400" />
                        {res.section}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3">
                    {res.page_number && (
                      <span className="px-2.5 py-0.5 bg-slate-800 text-slate-300 text-xs font-semibold rounded-md">
                        Page {res.page_number}
                      </span>
                    )}

                    <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">
                      <span className="text-xs font-bold text-emerald-400">{pct}% Match</span>
                    </div>
                  </div>
                </div>

                {/* Similarity Bar */}
                <div className="w-full bg-slate-950 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-full rounded-full transition-all duration-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>

                {/* Extracted Chunk Content */}
                <div className="bg-slate-950/80 rounded-lg p-3.5 border border-slate-900 text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed">
                  {res.text}
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-900/80 border-t border-slate-800 flex justify-between items-center shrink-0">
          <div className="text-xs text-slate-400">
            Model: <span className="font-mono text-indigo-300">BAAI/bge-small-en-v1.5</span> (384-dim)
          </div>
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold rounded-xl transition-colors"
          >
            Close Search
          </button>
        </div>
      </div>
    </div>
  );
}
