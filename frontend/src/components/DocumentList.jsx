import React, { useState } from 'react';
import { FileText, Eye, Trash2, Calendar, HardDrive, FileQuestion, Loader2, RefreshCw, Layers, Scan, AlertCircle, Search, CheckCircle2 } from 'lucide-react';
import DocumentDetailModal from './DocumentDetailModal';
import ChunkInspectorModal from './ChunkInspectorModal';
import DocumentSearchModal from './DocumentSearchModal';
import DocumentQAModal from './DocumentQAModal';
import DocumentAnalysisModal from './DocumentAnalysisModal';
import { documentApi } from '../services/documentApi';
import { Sparkles, FileSearch } from 'lucide-react';

export default function DocumentList({ documents, loading, error, onDocumentDeleted, onDocumentUpdated }) {
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [inspectDoc, setInspectDoc] = useState(null);
  const [searchDoc, setSearchDoc] = useState(null);
  const [qaDoc, setQaDoc] = useState(null);
  const [qaInitialQuestion, setQaInitialQuestion] = useState(null);
  const [analysisDoc, setAnalysisDoc] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [processingId, setProcessingId] = useState(null);

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const formatDate = (isoString) => {
    if (!isoString) return '';
    return new Date(isoString).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getCategoryBadgeClass = (category) => {
    switch (category?.toLowerCase()) {
      case 'legal':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30';
      case 'insurance':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'medical':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  const getEmbeddingBadge = (doc) => {
    const status = doc.embedding_status || 'pending';
    if (status === 'indexing') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
          <Loader2 className="w-3 h-3 animate-spin" />
          Indexing Vectors...
        </span>
      );
    }
    if (status === 'indexed') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3 h-3" />
          Indexed (ChromaDB)
        </span>
      );
    }
    if (status === 'failed') {
      return (
        <span
          title={doc.embedding_error || "Indexing failed"}
          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 cursor-help"
        >
          <AlertCircle className="w-3 h-3" />
          Indexing Failed
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">
        Index Pending
      </span>
    );
  };

  const handleProcess = async (docId) => {
    setProcessingId(docId);
    try {
      const updated = await documentApi.reprocessDocument(docId);
      if (onDocumentUpdated) onDocumentUpdated(updated);
    } catch (err) {
      alert(err.response?.data?.detail || "Processing failed.");
    } finally {
      setProcessingId(null);
    }
  };

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) return;

    setDeletingId(docId);
    try {
      await documentApi.deleteDocument(docId);
      if (onDocumentDeleted) onDocumentDeleted(docId);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete document.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="glass-card rounded-2xl p-6 sm:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-indigo-400" />
            My Documents
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Extract text/OCR, chunk content, generate embeddings, and search vectors.
          </p>
        </div>
        <span className="px-3 py-1 bg-slate-900 border border-slate-800 rounded-full text-xs font-semibold text-slate-400">
          {documents.length} {documents.length === 1 ? 'file' : 'files'}
        </span>
      </div>

      {loading && (
        <div className="py-12 flex flex-col items-center justify-center space-y-3 text-slate-400">
          <Loader2 className="w-7 h-7 animate-spin text-indigo-400" />
          <p className="text-sm">Fetching document library...</p>
        </div>
      )}

      {error && !loading && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm text-center">
          {error}
        </div>
      )}

      {!loading && !error && documents.length === 0 && (
        <div className="py-12 border-2 border-dashed border-slate-800 rounded-xl flex flex-col items-center justify-center text-center p-6 space-y-3">
          <div className="p-3 bg-slate-900 rounded-full text-slate-500">
            <FileQuestion className="w-8 h-8" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-300">No documents found</p>
            <p className="text-xs text-slate-500 mt-1">Upload your first document above to get started.</p>
          </div>
        </div>
      )}

      {!loading && documents.length > 0 && (
        <div className="space-y-3">
          {documents.map((doc) => {
            const isProcessing = processingId === doc.id || doc.status === 'processing' || doc.embedding_status === 'indexing';
            return (
              <div
                key={doc.id}
                className="glass-card-hover bg-slate-900/40 border border-slate-800/80 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="flex items-start gap-3.5 min-w-0">
                  <div className="p-2.5 bg-slate-800/80 rounded-xl text-indigo-400 border border-slate-700/50 shrink-0 mt-0.5 sm:mt-0">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div className="min-w-0 space-y-1">
                    <h4 className="text-sm font-bold text-white truncate max-w-md">
                      {doc.original_filename}
                    </h4>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border ${getCategoryBadgeClass(doc.document_type)}`}>
                        {doc.document_type}
                      </span>
                      {getEmbeddingBadge(doc)}
                      
                      {doc.has_ocr && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                          <Scan className="w-3 h-3" /> OCR Used
                        </span>
                      )}

                      <span className="text-xs text-slate-400 flex items-center gap-1">
                        <HardDrive className="w-3 h-3 text-slate-500" />
                        {formatBytes(doc.file_size)}
                      </span>
                      {doc.created_at && (
                        <span className="text-xs text-slate-400 flex items-center gap-1 hidden sm:flex">
                          <Calendar className="w-3 h-3 text-slate-500" />
                          {formatDate(doc.created_at)}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 shrink-0 self-end sm:self-center">
                  {doc.embedding_status === 'indexed' && (
                    <>
                      <button
                        onClick={() => setAnalysisDoc(doc)}
                        className="px-3 py-1.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl shadow-md shadow-blue-600/30 transition-all flex items-center gap-1.5"
                      >
                        <FileSearch className="w-3.5 h-3.5" />
                        Analyze
                      </button>
                      <button
                        onClick={() => setQaDoc(doc)}
                        className="px-3 py-1.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-semibold rounded-xl shadow-md shadow-purple-600/30 transition-all flex items-center gap-1.5"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        Ask AI
                      </button>
                      <button
                        onClick={() => setSearchDoc(doc)}
                        className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700/80 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700/60 transition-colors flex items-center gap-1.5"
                      >
                        <Search className="w-3.5 h-3.5 text-indigo-400" />
                        Search
                      </button>
                    </>
                  )}

                  {doc.status === 'ready' && (
                    <button
                      onClick={() => setInspectDoc(doc)}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700/80 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700/60 transition-colors flex items-center gap-1.5"
                    >
                      <Layers className="w-3.5 h-3.5 text-indigo-400" />
                      Chunks
                    </button>
                  )}

                  <button
                    onClick={() => handleProcess(doc.id)}
                    disabled={isProcessing}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700/80 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700/60 transition-colors flex items-center gap-1.5 disabled:opacity-50"
                  >
                    {isProcessing ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
                    )}
                    {doc.status === 'ready' ? 'Re-index' : 'Process'}
                  </button>

                  <button
                    onClick={() => setSelectedDoc(doc)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700/80 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700/60 transition-colors flex items-center gap-1.5"
                  >
                    <Eye className="w-3.5 h-3.5 text-slate-400" />
                    Meta
                  </button>

                  <button
                    onClick={() => handleDelete(doc.id, doc.original_filename)}
                    disabled={deletingId === doc.id}
                    className="px-2.5 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 text-xs font-semibold rounded-xl border border-rose-500/20 transition-colors flex items-center gap-1.5 disabled:opacity-50"
                  >
                    {deletingId === doc.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Trash2 className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selectedDoc && (
        <DocumentDetailModal
          document={selectedDoc}
          onClose={() => setSelectedDoc(null)}
        />
      )}

      {inspectDoc && (
        <ChunkInspectorModal
          document={inspectDoc}
          onClose={() => setInspectDoc(null)}
        />
      )}

      {searchDoc && (
        <DocumentSearchModal
          document={searchDoc}
          onClose={() => setSearchDoc(null)}
        />
      )}

      {qaDoc && (
        <DocumentQAModal
          document={qaDoc}
          initialQuestion={qaInitialQuestion}
          onClose={() => {
            setQaDoc(null);
            setQaInitialQuestion(null);
          }}
        />
      )}

      {analysisDoc && (
        <DocumentAnalysisModal
          document={analysisDoc}
          onClose={() => setAnalysisDoc(null)}
          onSelectQuestion={(qText) => {
            setQaDoc(analysisDoc);
            setQaInitialQuestion(qText);
            setAnalysisDoc(null);
          }}
        />
      )}
    </div>
  );
}
