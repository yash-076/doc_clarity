import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { documentApi } from '../services/documentApi';

const DOMAIN_CATEGORIES = [
  { id: 'legal', label: 'Legal', color: 'indigo' },
  { id: 'insurance', label: 'Insurance', color: 'blue' },
  { id: 'medical', label: 'Medical', color: 'emerald' },
  { id: 'other', label: 'Other', color: 'slate' },
];

const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt'];
const MAX_FILE_SIZE_MB = 20;

export default function DocumentUpload({ onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [documentType, setDocumentType] = useState('legal');
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  const fileInputRef = useRef(null);

  const validateLocalFile = (file) => {
    if (!file) return false;
    
    if (file.size === 0) {
      setErrorMsg("File is empty. Please select a valid document.");
      return false;
    }

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setErrorMsg(`File size exceeds maximum allowed limit of ${MAX_FILE_SIZE_MB} MB.`);
      return false;
    }

    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setErrorMsg(`Unsupported file type '${ext}'. Allowed formats: PDF, DOCX, TXT.`);
      return false;
    }

    setErrorMsg(null);
    return true;
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file && validateLocalFile(file)) {
      setSelectedFile(file);
      setSuccessMsg(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file && validateLocalFile(file)) {
      setSelectedFile(file);
      setSuccessMsg(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setErrorMsg("Please select a document to upload.");
      return;
    }

    setUploading(true);
    setProgress(0);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      await documentApi.uploadDocument(selectedFile, documentType, (pct) => {
        setProgress(pct);
      });

      setSuccessMsg("Document uploaded successfully.");
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      if (onUploadSuccess) onUploadSuccess();
    } catch (err) {
      const serverDetail = err.response?.data?.detail;
      setErrorMsg(serverDetail || "Upload failed. Please check backend connection.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="glass-card rounded-2xl p-6 sm:p-8 space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-indigo-400" />
          Upload Document
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Select document type and upload files for intelligent analysis.
        </p>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-300 ${
          isDragging
            ? 'border-indigo-500 bg-indigo-500/10 scale-[1.01]'
            : selectedFile
            ? 'border-emerald-500/50 bg-emerald-500/5'
            : 'border-slate-700/60 bg-slate-900/40 hover:border-indigo-500/50 hover:bg-slate-900/80'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf,.docx,.txt"
          className="hidden"
        />

        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="p-3 bg-indigo-500/10 rounded-full text-indigo-400 border border-indigo-500/20">
            <FileText className="w-8 h-8" />
          </div>

          {selectedFile ? (
            <div>
              <p className="text-sm font-semibold text-emerald-400">
                {selectedFile.name}
              </p>
              <p className="text-xs text-slate-400 mt-1">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB — Ready to upload
              </p>
            </div>
          ) : (
            <div>
              <p className="text-sm font-medium text-slate-200">
                Drag & drop or <span className="text-indigo-400 font-semibold underline underline-offset-4">choose a file</span>
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Supported formats: PDF / DOCX / TXT — Max size: 20 MB
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Document Type Selector */}
      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
          Document Type
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {DOMAIN_CATEGORIES.map((cat) => {
            const isSelected = documentType === cat.id;
            return (
              <button
                key={cat.id}
                type="button"
                onClick={() => setDocumentType(cat.id)}
                className={`py-2.5 px-4 rounded-xl font-medium text-sm transition-all duration-200 border ${
                  isSelected
                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-lg shadow-indigo-600/30'
                    : 'bg-slate-900/60 text-slate-400 border-slate-800 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                {cat.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Upload Progress Bar */}
      {uploading && (
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-semibold text-slate-400">
            <span>Uploading...</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
            <div
              className="bg-indigo-500 h-full transition-all duration-300 rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Alert Banners */}
      {errorMsg && (
        <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-400 text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-3 text-emerald-400 text-sm">
          <CheckCircle2 className="w-5 h-5 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Action Button */}
      <button
        type="button"
        onClick={handleUpload}
        disabled={!selectedFile || uploading}
        className={`w-full py-3.5 px-6 rounded-xl font-semibold text-sm transition-all duration-300 flex items-center justify-center gap-2 ${
          !selectedFile || uploading
            ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
            : 'bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 active:scale-[0.99]'
        }`}
      >
        {uploading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Uploading Document...
          </>
        ) : (
          'Upload Document'
        )}
      </button>
    </div>
  );
}
