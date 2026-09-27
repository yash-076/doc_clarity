import React, { useState, useEffect } from 'react';
import { X, Layers, Loader2, FileCode, Tag, Sparkles, AlertCircle } from 'lucide-react';
import { documentApi } from '../services/documentApi';

export default function ChunkInspectorModal({ document, onClose }) {
  const [chunksData, setChunksData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!document) return;
    setLoading(true);
    setError(null);
    documentApi.fetchDocumentChunks(document.id)
      .then((data) => setChunksData(data))
      .catch((err) => setError(err.response?.data?.detail || "Failed to fetch document chunks."))
      .finally(() => setLoading(false));
  }, [document]);

  if (!document) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="glass-card rounded-2xl w-full max-w-4xl h-[85vh] flex flex-col overflow-hidden border border-slate-700/80 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-900/60 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                Chunk Inspector
                <span className="text-xs font-semibold px-2.5 py-0.5 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full">
                  {chunksData ? `${chunksData.total_chunks} chunks` : 'Loading...'}
                </span>
              </h3>
              <p className="text-xs text-slate-400 truncate max-w-md mt-0.5">
                {document.original_filename}
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

        {/* Content Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {loading && (
            <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
              <p className="text-sm font-medium">Extracting and loading semantic chunks...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm flex items-center gap-2">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          )}

          {!loading && !error && chunksData && chunksData.chunks.length === 0 && (
            <div className="py-16 text-center text-slate-400 text-sm">
              No chunks generated for this document.
            </div>
          )}

          {!loading && !error && chunksData && chunksData.chunks.map((chunk) => (
            <div
              key={chunk.id}
              className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-3 hover:border-slate-700 transition-colors"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-1 bg-indigo-500/10 text-indigo-400 font-mono text-xs font-bold rounded-lg border border-indigo-500/20">
                    Chunk #{chunk.chunk_index}
                  </span>
                  {chunk.section && (
                    <span className="text-xs font-semibold text-slate-300 flex items-center gap-1">
                      <Tag className="w-3 h-3 text-slate-400" />
                      {chunk.section}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {chunk.page_number && (
                    <span className="px-2 py-0.5 bg-slate-800 text-slate-300 text-xs font-medium rounded-md">
                      Page {chunk.page_number}
                    </span>
                  )}

                  <span className={`px-2 py-0.5 text-xs font-semibold rounded-md border ${
                    chunk.extraction_method === 'ocr'
                      ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                      : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  }`}>
                    {chunk.extraction_method === 'ocr' ? 'OCR Extracted' : 'Native Text'}
                  </span>
                </div>
              </div>

              {/* Chunk Text */}
              <div className="bg-slate-950/80 rounded-lg p-3.5 border border-slate-900 text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed">
                {chunk.text}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-900/80 border-t border-slate-800 flex justify-between items-center shrink-0">
          <div className="text-xs text-slate-400 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Ready for ChromaDB / Vector Store ingestion
          </div>
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold rounded-xl transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
