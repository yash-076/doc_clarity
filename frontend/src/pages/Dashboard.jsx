import React, { useState, useEffect, useCallback } from 'react';
import { Shield, Sparkles } from 'lucide-react';
import DocumentUpload from '../components/DocumentUpload';
import DocumentList from '../components/DocumentList';
import { documentApi } from '../services/documentApi';

export default function Dashboard() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await documentApi.fetchDocuments();
      setDocuments(data);
    } catch (err) {
      console.error('Failed to load documents:', err);
      setError('Could not connect to backend server. Please verify FastAPI is running.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleDocumentDeleted = (deletedId) => {
    setDocuments((prev) => prev.filter((d) => d.id !== deletedId));
  };

  const handleDocumentUpdated = (updatedDoc) => {
    setDocuments((prev) =>
      prev.map((d) => (d.id === updatedDoc.id ? updatedDoc : d))
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white pb-16">
      {/* Navbar / Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-tr from-indigo-600 to-indigo-400 rounded-xl shadow-lg shadow-indigo-500/20 text-white">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                Doc Clarity
                <span className="text-[10px] font-semibold px-2 py-0.5 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full">
                  Phase 3: Embeddings & ChromaDB
                </span>
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex items-center gap-2 text-xs font-semibold text-slate-400 bg-slate-900 px-3.5 py-1.5 rounded-full border border-slate-800">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              Document Intelligence Platform
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-10 space-y-8">
        {/* Banner */}
        <div className="text-center space-y-2">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-slate-400">
            Vector Indexing & Semantic Retrieval
          </h2>
          <p className="text-slate-400 text-sm sm:text-base max-w-xl mx-auto">
            Generate local dense vector embeddings with <span className="text-indigo-400 font-medium">BAAI/bge-small-en-v1.5</span>, store in persistent ChromaDB, and perform document-isolated similarity search.
          </p>
        </div>

        {/* Section 1: Upload */}
        <DocumentUpload onUploadSuccess={fetchDocuments} />

        {/* Section 2: My Documents */}
        <DocumentList
          documents={documents}
          loading={loading}
          error={error}
          onDocumentDeleted={handleDocumentDeleted}
          onDocumentUpdated={handleDocumentUpdated}
        />
      </main>
    </div>
  );
}
