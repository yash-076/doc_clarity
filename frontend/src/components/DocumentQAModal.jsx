import React, { useState } from 'react';
import { X, Sparkles, Send, Loader2, BookOpen, AlertTriangle, ShieldCheck, CheckCircle2, FileText, Info } from 'lucide-react';
import { documentApi } from '../services/documentApi';

export default function DocumentQAModal({ document, onClose }) {
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(5);
  const [asking, setAsking] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);

  if (!document) return null;

  const sampleQuestions = [
    "What are the main exclusions or limitations mentioned in this document?",
    "What are the key obligations, conditions, or terms specified?",
    "What are the important dates, deadlines, or monetary amounts?",
  ];

  const handleAsk = async (e, customQ = null) => {
    if (e) e.preventDefault();
    const qToAsk = customQ || question;
    if (!qToAsk.trim()) return;

    if (customQ) {
      setQuestion(customQ);
    }

    setAsking(true);
    setError(null);

    try {
      const data = await documentApi.askDocument(document.id, qToAsk.trim(), topK);
      setResponse(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate answer from document.");
    } finally {
      setAsking(false);
    }
  };

  const getConfidenceBadge = (confidence) => {
    switch (confidence) {
      case 'high':
        return (
          <span className="px-3 py-1 bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 rounded-full text-xs font-semibold flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" /> High Grounded Confidence
          </span>
        );
      case 'medium':
        return (
          <span className="px-3 py-1 bg-amber-500/15 text-amber-400 border border-amber-500/30 rounded-full text-xs font-semibold flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5" /> Medium Confidence
          </span>
        );
      case 'low':
      default:
        return (
          <span className="px-3 py-1 bg-rose-500/15 text-rose-400 border border-rose-500/30 rounded-full text-xs font-semibold flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" /> Low / Unverified Evidence
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="glass-card rounded-2xl w-full max-w-4xl h-[90vh] flex flex-col overflow-hidden border border-slate-700/80 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-900/60 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-purple-500/10 text-purple-400 rounded-xl border border-purple-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                Document Q&A Assistant
                <span className="text-xs font-semibold px-2.5 py-0.5 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full">
                  Gemini Grounded RAG
                </span>
              </h3>
              <p className="text-xs text-slate-400 truncate max-w-md mt-0.5">
                Target Document: <span className="text-slate-200 font-semibold">{document.original_filename}</span>
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

        {/* Form Controls */}
        <div className="p-6 bg-slate-900/40 border-b border-slate-800 shrink-0 space-y-4">
          <form onSubmit={(e) => handleAsk(e)} className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask any question grounded strictly in this document..."
                className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
              />
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <div className="flex items-center gap-2 bg-slate-950/80 border border-slate-700/80 px-3 py-2 rounded-xl text-xs font-semibold text-slate-400">
                <span>Top K Context:</span>
                <select
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                  className="bg-transparent text-purple-400 font-bold focus:outline-none cursor-pointer"
                >
                  <option value={3}>3</option>
                  <option value={5}>5</option>
                  <option value={8}>8</option>
                  <option value={10}>10</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={!question.trim() || asking}
                className={`py-2.5 px-6 rounded-xl font-semibold text-sm transition-all duration-200 flex items-center gap-2 ${
                  !question.trim() || asking
                    ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                    : 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/30'
                }`}
              >
                {asking ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    <span>Ask AI</span>
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Quick Prompts */}
          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-xs text-slate-500 font-medium">Quick Prompts:</span>
            {sampleQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={(e) => handleAsk(e, q)}
                disabled={asking}
                className="text-xs bg-slate-800/60 hover:bg-slate-800 text-slate-300 hover:text-purple-300 px-3 py-1 rounded-lg border border-slate-700/60 transition-colors truncate max-w-xs"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold">Generation Error</h4>
                <p className="mt-0.5 text-xs text-rose-300">{error}</p>
              </div>
            </div>
          )}

          {!response && !asking && !error && (
            <div className="flex flex-col items-center justify-center h-full text-center p-12 text-slate-500 space-y-3">
              <div className="p-4 bg-slate-900/60 rounded-2xl border border-slate-800 text-slate-400">
                <BookOpen className="w-8 h-8 text-purple-400/80" />
              </div>
              <h4 className="text-base font-semibold text-slate-300">Grounded Question Answering</h4>
              <p className="text-xs text-slate-400 max-w-md leading-relaxed">
                Type a question above or select a quick prompt. The system will retrieve relevant document chunks using local dense embeddings and generate a grounded answer with Gemini LLM.
              </p>
            </div>
          )}

          {asking && (
            <div className="flex flex-col items-center justify-center py-16 text-center space-y-4">
              <div className="relative">
                <div className="w-12 h-12 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></div>
                <Sparkles className="w-5 h-5 text-purple-400 absolute inset-0 m-auto" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-200">Retrieving Document Context & Generating Answer</h4>
                <p className="text-xs text-slate-400 mt-1">Filtering ChromaDB vectors for document isolation...</p>
              </div>
            </div>
          )}

          {response && !asking && (
            <div className="space-y-6 animate-fadeIn">
              {/* Answer Card */}
              <div className="p-6 bg-slate-900/70 border border-slate-800 rounded-2xl space-y-4 shadow-lg">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-purple-400" />
                    <h4 className="text-sm font-bold text-white">Grounded Answer</h4>
                  </div>
                  {getConfidenceBadge(response.confidence)}
                </div>

                <div className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap font-sans">
                  {response.answer}
                </div>

                {response.disclaimer && (
                  <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-400 flex items-start gap-2.5">
                    <ShieldCheck className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                    <span>{response.disclaimer}</span>
                  </div>
                )}
              </div>

              {/* Citations / Sources */}
              <div>
                <h4 className="text-sm font-bold text-slate-300 mb-3 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-indigo-400" />
                  Source Citations ({response.citations?.length || 0})
                </h4>

                {(!response.citations || response.citations.length === 0) ? (
                  <div className="p-4 bg-slate-900/30 border border-slate-800/80 rounded-xl text-xs text-slate-500">
                    No explicit source citations retrieved for this answer.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {response.citations.map((citation, idx) => (
                      <div
                        key={idx}
                        className="p-4 bg-slate-900/40 border border-slate-800 hover:border-slate-700/80 rounded-xl space-y-2 transition-colors"
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-purple-300">
                            Source #{idx + 1}
                          </span>
                          <span className="px-2 py-0.5 bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded font-mono font-bold">
                            {(citation.relevance_score * 100).toFixed(0)}% match
                          </span>
                        </div>

                        <div className="flex flex-wrap gap-2 text-xs text-slate-400 pt-1">
                          {citation.page_number && (
                            <span className="px-2 py-0.5 bg-slate-800 rounded text-slate-300 font-medium">
                              Page {citation.page_number}
                            </span>
                          )}
                          {citation.section && (
                            <span className="px-2 py-0.5 bg-slate-800 rounded text-slate-300 font-medium truncate max-w-[180px]">
                              Section: {citation.section}
                            </span>
                          )}
                          <span className="px-2 py-0.5 bg-slate-800/50 rounded text-slate-500 font-mono text-[10px]">
                            Chunk: {citation.chunk_id.slice(0, 8)}...
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
