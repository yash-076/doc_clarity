import React from 'react';
import { X, FileText, Calendar, HardDrive, Hash, ShieldCheck, Tag } from 'lucide-react';

export default function DocumentDetailModal({ document, onClose }) {
  if (!document) return null;

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (isoString) => {
    if (!isoString) return 'N/A';
    return new Date(isoString).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short'
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="glass-card rounded-2xl w-full max-w-lg overflow-hidden border border-slate-700/80 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-800 bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white leading-tight">Document Details</h3>
              <p className="text-xs text-slate-400">Metadata inspection view</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          <div className="bg-slate-900/60 rounded-xl p-4 border border-slate-800 space-y-3">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Original Filename</span>
              <p className="text-sm font-bold text-white break-all mt-0.5">{document.original_filename}</p>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-800/60">
              <div>
                <span className="text-xs text-slate-400 flex items-center gap-1.5">
                  <Tag className="w-3.5 h-3.5 text-indigo-400" /> Category
                </span>
                <p className="text-sm font-semibold text-slate-200 capitalize mt-1">{document.document_type}</p>
              </div>
              <div>
                <span className="text-xs text-slate-400 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Status
                </span>
                <p className="text-sm font-semibold text-emerald-400 capitalize mt-1">{document.status}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-800/60">
              <div>
                <span className="text-xs text-slate-400 flex items-center gap-1.5">
                  <HardDrive className="w-3.5 h-3.5 text-blue-400" /> File Size
                </span>
                <p className="text-sm font-semibold text-slate-200 mt-1">{formatBytes(document.file_size)}</p>
              </div>
              <div>
                <span className="text-xs text-slate-400 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-violet-400" /> Uploaded At
                </span>
                <p className="text-sm font-semibold text-slate-200 mt-1">{formatDate(document.created_at)}</p>
              </div>
            </div>
          </div>

          <div className="space-y-2 text-xs text-slate-400">
            <div className="flex justify-between items-center bg-slate-900/40 p-2.5 rounded-lg border border-slate-800/50">
              <span className="font-semibold text-slate-400 flex items-center gap-1">
                <Hash className="w-3.5 h-3.5 text-slate-500" /> Document ID
              </span>
              <span className="font-mono text-slate-300 break-all">{document.id}</span>
            </div>
            {document.mime_type && (
              <div className="flex justify-between items-center bg-slate-900/40 p-2.5 rounded-lg border border-slate-800/50">
                <span className="font-semibold text-slate-400">MIME Type</span>
                <span className="font-mono text-slate-300">{document.mime_type}</span>
              </div>
            )}
            {document.stored_filename && (
              <div className="flex justify-between items-center bg-slate-900/40 p-2.5 rounded-lg border border-slate-800/50">
                <span className="font-semibold text-slate-400">Stored Name</span>
                <span className="font-mono text-slate-300">{document.stored_filename}</span>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-900/80 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold rounded-xl transition-colors"
          >
            Close Metadata
          </button>
        </div>
      </div>
    </div>
  );
}
