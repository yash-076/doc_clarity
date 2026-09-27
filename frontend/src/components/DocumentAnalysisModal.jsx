import React, { useState, useEffect } from 'react';
import { X, FileSearch, RefreshCw, Loader2, AlertTriangle, Calendar, DollarSign, ShieldAlert, CheckCircle2, FileText, UserCheck, AlertCircle, Info, Tag } from 'lucide-react';
import { documentApi } from '../services/documentApi';

export default function DocumentAnalysisModal({ document, onClose }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');

  if (!document) return null;

  const loadAnalysis = async (forceRefresh = false) => {
    if (forceRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);

    try {
      const data = await documentApi.analyzeDocument(document.id, forceRefresh);
      setAnalysis(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate document analysis.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadAnalysis(false);
  }, [document.id]);

  const getSeverityBadge = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high':
        return (
          <span className="px-2.5 py-1 bg-rose-500/15 text-rose-400 border border-rose-500/30 rounded-full text-xs font-bold flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" /> High Attention
          </span>
        );
      case 'medium':
        return (
          <span className="px-2.5 py-1 bg-amber-500/15 text-amber-400 border border-amber-500/30 rounded-full text-xs font-bold flex items-center gap-1">
            <Info className="w-3.5 h-3.5" /> Medium Attention
          </span>
        );
      case 'low':
      default:
        return (
          <span className="px-2.5 py-1 bg-slate-500/15 text-slate-400 border border-slate-500/30 rounded-full text-xs font-bold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> Low Attention
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="glass-card rounded-2xl w-full max-w-5xl h-[90vh] flex flex-col overflow-hidden border border-slate-700/80 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-900/60 shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-500/10 text-blue-400 rounded-xl border border-blue-500/20">
              <FileSearch className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                Automatic Document Analysis
                <span className="text-xs font-semibold px-2.5 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-full capitalize">
                  {document.document_type} Domain
                </span>
                {analysis?.is_stale && (
                  <span className="text-xs font-semibold px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full">
                    Stale (Content Changed)
                  </span>
                )}
              </h3>
              <p className="text-xs text-slate-400 truncate max-w-md mt-0.5">
                Target Document: <span className="text-slate-200 font-semibold">{document.original_filename}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => loadAnalysis(true)}
              disabled={loading || refreshing}
              className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700/80 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700/60 transition-colors flex items-center gap-1.5 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-blue-400' : 'text-slate-400'}`} />
              {refreshing ? 'Analyzing...' : 'Re-Analyze'}
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 p-3 px-6 bg-slate-900/40 border-b border-slate-800 shrink-0 overflow-x-auto text-xs font-semibold">
          <button
            onClick={() => setActiveTab('summary')}
            className={`px-4 py-2 rounded-xl transition-colors ${
              activeTab === 'summary' ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            Executive Summary
          </button>
          <button
            onClick={() => setActiveTab('attention')}
            className={`px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5 ${
              activeTab === 'attention' ? 'bg-rose-600 text-white shadow-md shadow-rose-600/30' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            Attention & Risks ({analysis?.attention_items?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('keypoints')}
            className={`px-4 py-2 rounded-xl transition-colors ${
              activeTab === 'keypoints' ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            Key Points ({analysis?.key_points?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('financials')}
            className={`px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5 ${
              activeTab === 'financials' ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <DollarSign className="w-3.5 h-3.5" />
            Financials ({analysis?.financial_terms?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('dates')}
            className={`px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5 ${
              activeTab === 'dates' ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Calendar className="w-3.5 h-3.5" />
            Dates ({analysis?.important_dates?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('obligations')}
            className={`px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5 ${
              activeTab === 'obligations' ? 'bg-amber-600 text-white shadow-md shadow-amber-600/30' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <UserCheck className="w-3.5 h-3.5" />
            Obligations ({analysis?.obligations?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('exclusions')}
            className={`px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5 ${
              activeTab === 'exclusions' ? 'bg-slate-700 text-white shadow-md' : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            Exclusions ({analysis?.exclusions?.length || 0})
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold">Analysis Error</h4>
                <p className="mt-0.5 text-xs text-rose-300">{error}</p>
              </div>
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
              <div className="relative">
                <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin"></div>
                <FileSearch className="w-5 h-5 text-blue-400 absolute inset-0 m-auto" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-200">Analyzing Document Facets with Gemini LLM</h4>
                <p className="text-xs text-slate-400 mt-1">Running multi-query targeted retrieval across dates, terms, and risk items...</p>
              </div>
            </div>
          )}

          {!loading && analysis && (
            <div className="space-y-6 animate-fadeIn">
              {/* SUMMARY TAB */}
              {activeTab === 'summary' && (
                <div className="p-6 bg-slate-900/70 border border-slate-800 rounded-2xl space-y-4 shadow-lg">
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                    <h4 className="text-sm font-bold text-white flex items-center gap-2">
                      <FileText className="w-4 h-4 text-blue-400" />
                      Executive Summary
                    </h4>
                    <span className="text-xs text-slate-500 font-mono">
                      Model: {analysis.llm_model || 'Gemini'}
                    </span>
                  </div>
                  <p className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap font-sans">
                    {analysis.summary}
                  </p>
                </div>
              )}

              {/* ATTENTION & RISKS TAB */}
              {activeTab === 'attention' && (
                <div className="space-y-4">
                  {(!analysis.attention_items || analysis.attention_items.length === 0) ? (
                    <div className="p-6 bg-slate-900/30 border border-slate-800 rounded-xl text-center text-slate-500 text-sm">
                      No explicit high-attention or concerning items detected in this document.
                    </div>
                  ) : (
                    analysis.attention_items.map((item, idx) => (
                      <div key={idx} className="p-5 bg-slate-900/60 border border-slate-800 rounded-2xl space-y-3 shadow-md">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-bold text-white flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4 text-amber-400" />
                            {item.title}
                          </h4>
                          <div className="flex items-center gap-2">
                            <span className="px-2.5 py-0.5 bg-slate-800 text-slate-300 border border-slate-700 rounded-full text-xs font-semibold capitalize">
                              {item.category.replace('_', ' ')}
                            </span>
                            {getSeverityBadge(item.severity)}
                          </div>
                        </div>

                        <p className="text-xs text-slate-300 leading-relaxed">
                          {item.description}
                        </p>

                        {item.citations && item.citations.length > 0 && (
                          <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800/60">
                            {item.citations.map((c, cIdx) => (
                              <span key={cIdx} className="text-[11px] px-2.5 py-0.5 bg-slate-800/80 text-slate-400 rounded-md border border-slate-700/60 flex items-center gap-1 font-mono">
                                <Tag className="w-3 h-3 text-slate-500" />
                                {c.page_number ? `Page ${c.page_number}` : 'Source'} {c.section ? `• ${c.section}` : ''}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* KEY POINTS TAB */}
              {activeTab === 'keypoints' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {analysis.key_points.map((kp, idx) => (
                    <div key={idx} className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
                      <h5 className="text-sm font-bold text-indigo-300">{kp.title}</h5>
                      <p className="text-xs text-slate-300 leading-relaxed">{kp.description}</p>
                      {kp.citations && kp.citations.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {kp.citations.map((c, cIdx) => (
                            <span key={cIdx} className="text-[10px] px-2 py-0.5 bg-slate-800 text-slate-400 rounded">
                              Page {c.page_number || 'N/A'} {c.section ? `(${c.section})` : ''}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* FINANCIALS TAB */}
              {activeTab === 'financials' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {analysis.financial_terms.map((ft, idx) => (
                    <div key={idx} className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
                      <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">{ft.description}</div>
                      <div className="text-lg font-bold text-white">{ft.amount || 'Specified in text'}</div>
                      {ft.citations && ft.citations.length > 0 && (
                        <div className="text-[10px] text-slate-500 pt-1">
                          Page {ft.citations[0].page_number || 'N/A'} {ft.citations[0].section ? `• ${ft.citations[0].section}` : ''}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* DATES TAB */}
              {activeTab === 'dates' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {analysis.important_dates.map((dt, idx) => (
                    <div key={idx} className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
                      <div className="text-xs font-semibold text-purple-400">{dt.description}</div>
                      <div className="text-sm font-bold text-white">{dt.date || 'Specified timeframe'}</div>
                      {dt.citations && dt.citations.length > 0 && (
                        <div className="text-[10px] text-slate-500 pt-1">
                          Page {dt.citations[0].page_number || 'N/A'} {dt.citations[0].section ? `• ${dt.citations[0].section}` : ''}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* OBLIGATIONS TAB */}
              {activeTab === 'obligations' && (
                <div className="space-y-3">
                  {analysis.obligations.map((ob, idx) => (
                    <div key={idx} className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1.5">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[11px] font-bold rounded-md">
                          {ob.party}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">{ob.description}</p>
                      {ob.citations && ob.citations.length > 0 && (
                        <div className="text-[10px] text-slate-500 pt-1">
                          Page {ob.citations[0].page_number || 'N/A'} {ob.citations[0].section ? `• ${ob.citations[0].section}` : ''}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* EXCLUSIONS TAB */}
              {activeTab === 'exclusions' && (
                <div className="space-y-3">
                  {analysis.exclusions.map((ex, idx) => (
                    <div key={idx} className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1.5">
                      <p className="text-xs text-slate-300 leading-relaxed">{ex.description}</p>
                      {ex.citations && ex.citations.length > 0 && (
                        <div className="text-[10px] text-slate-500 pt-1">
                          Page {ex.citations[0].page_number || 'N/A'} {ex.citations[0].section ? `• ${ex.citations[0].section}` : ''}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
