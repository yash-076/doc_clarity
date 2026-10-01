import { useState, useEffect, useCallback } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import {
  FileText,
  Upload,
  Search,
  Shield,
  Heart,
  Scale,
  Clock,
  HardDrive,
  CheckCircle,
  AlertCircle,
  Loader,
  Trash2,
  BarChart3,
  Plus,
  RefreshCw,
  FileUp,
  X,
} from 'lucide-react'
import { listDocuments, uploadDocument, deleteDocument } from '../services/api'
import './DashboardPage.css'

const DOC_TYPE_ICONS = {
  legal: Scale,
  insurance: Shield,
  medical: Heart,
  other: FileText,
}

const STATUS_MAP = {
  completed: { label: 'Processed', class: 'badge-success', icon: CheckCircle },
  processing: { label: 'Processing', class: 'badge-warning', icon: Loader },
  failed: { label: 'Failed', class: 'badge-error', icon: AlertCircle },
  uploaded: { label: 'Uploaded', class: 'badge-info', icon: FileUp },
}

const EMBEDDING_MAP = {
  indexed: { label: 'AI Ready', class: 'badge-success' },
  pending: { label: 'Preparing', class: 'badge-warning' },
  failed: { label: 'Setup Failed', class: 'badge-error' },
}

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

export default function DashboardPage() {
  const location = useLocation()
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [docType, setDocType] = useState('legal')
  const [error, setError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')

  // Load documents
  const fetchDocuments = useCallback(async () => {
    try {
      setLoading(true)
      const data = await listDocuments()
      setDocuments(data)
    } catch (err) {
      setError('Failed to load documents. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  // Open upload zone if navigated with state
  useEffect(() => {
    if (location.state?.openUpload) {
      setSelectedFile(null) // just show the zone
    }
  }, [location.state])

  // Dropzone
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0])
      setError(null)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/tiff': ['.tiff', '.tif'],
    },
    maxFiles: 1,
    maxSize: 20 * 1024 * 1024,
  })

  // Upload handler
  const handleUpload = async () => {
    if (!selectedFile) return
    try {
      setUploading(true)
      setError(null)
      await uploadDocument(selectedFile, docType)
      setSelectedFile(null)
      await fetchDocuments()
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  // Delete handler
  const handleDelete = async (e, id) => {
    e.preventDefault()
    e.stopPropagation()
    if (!confirm('Are you sure you want to delete this document?')) return
    try {
      await deleteDocument(id)
      setDocuments((prev) => prev.filter((d) => d.id !== id))
    } catch (err) {
      setError('Failed to delete document.')
    }
  }

  // Stats
  const totalDocs = documents.length
  const processedDocs = documents.filter((d) => d.status === 'completed').length
  const indexedDocs = documents.filter((d) => d.embedding_status === 'indexed').length
  const totalSize = documents.reduce((sum, d) => sum + (d.file_size || 0), 0)

  // Filter
  const filteredDocs = documents.filter((d) =>
    d.original_filename?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="animate-fadeIn">
      {/* Header */}
      <div className="dashboard-header">
        <div className="dashboard-header-left">
          <h1>Dashboard</h1>
          <p>Manage and analyze your documents with AI-powered intelligence</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchDocuments} id="refresh-docs-btn">
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        {[
          { icon: FileText, label: 'Total Documents', value: totalDocs, color: 'green' },
          { icon: CheckCircle, label: 'Processed', value: processedDocs, color: 'blue' },
          { icon: BarChart3, label: 'AI Ready', value: indexedDocs, color: 'yellow' },
          { icon: HardDrive, label: 'Total Size', value: formatBytes(totalSize), color: 'purple' },
        ].map((s, i) => (
          <div className="stat-card" key={i}>
            <div className="stat-card-header">
              <div className={`stat-card-icon ${s.color}`}>
                <s.icon size={20} />
              </div>
            </div>
            <div className="stat-card-value">{s.value}</div>
            <div className="stat-card-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="toast toast-error" style={{ position: 'relative', marginBottom: 'var(--space-4)' }}>
          <AlertCircle size={18} />
          <span style={{ flex: 1 }}>{error}</span>
          <button className="btn btn-ghost btn-sm" onClick={() => setError(null)}>
            <X size={14} />
          </button>
        </div>
      )}

      {/* Upload Zone */}
      {!selectedFile ? (
        <div
          {...getRootProps()}
          className={`upload-zone ${isDragActive ? 'active' : ''}`}
          id="upload-dropzone"
        >
          <input {...getInputProps()} id="file-input" />
          <div className="upload-zone-icon">
            <Upload size={28} />
          </div>
          <div className="upload-zone-title">
            {isDragActive ? 'Drop your document here...' : 'Drag & drop your document here'}
          </div>
          <div className="upload-zone-desc">
            or click to browse files from your computer
          </div>
          <div className="upload-zone-formats">
            <span className="badge badge-neutral">PDF</span>
            <span className="badge badge-neutral">PNG</span>
            <span className="badge badge-neutral">JPG</span>
            <span className="badge badge-neutral">TIFF</span>
            <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-xs)' }}>
              Max 20 MB
            </span>
          </div>
        </div>
      ) : (
        <div className="upload-form" id="upload-form">
          <div className="upload-form-file">
            <div className="upload-form-file-icon">
              <FileText size={24} />
            </div>
            <div className="upload-form-file-info">
              <div className="upload-form-file-name">{selectedFile.name}</div>
              <div className="upload-form-file-size">{formatBytes(selectedFile.size)}</div>
            </div>
            <button className="btn btn-ghost btn-icon" onClick={() => setSelectedFile(null)}>
              <X size={18} />
            </button>
          </div>
          <div className="upload-form-controls">
            <div className="input-group" style={{ flex: 1 }}>
              <label className="input-label">Document Type</label>
              <select
                className="input"
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                id="doc-type-select"
              >
                <option value="legal">Legal</option>
                <option value="insurance">Insurance</option>
                <option value="medical">Medical</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div className="upload-form-actions">
            <button className="btn btn-secondary" onClick={() => setSelectedFile(null)}>
              Cancel
            </button>
            <button
              className="btn btn-primary"
              onClick={handleUpload}
              disabled={uploading}
              id="upload-submit-btn"
            >
              {uploading ? (
                <>
                  <span className="spinner" /> Uploading...
                </>
              ) : (
                <>
                  <Upload size={16} /> Upload & Process
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Documents List */}
      <div className="docs-section-header">
        <h2 className="docs-section-title">Your Documents</h2>
        <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
          <div style={{ position: 'relative' }}>
            <Search
              size={16}
              style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--color-text-muted)',
              }}
            />
            <input
              className="input"
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ paddingLeft: '36px', width: '240px' }}
              id="search-documents-input"
            />
          </div>
        </div>
      </div>

      {loading ? (
        <div className="loading-grid">
          {[1, 2, 3].map((i) => (
            <div className="loading-card skeleton" key={i} />
          ))}
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">
            <FileText size={36} />
          </div>
          <h3>{searchQuery ? 'No matching documents' : 'No documents yet'}</h3>
          <p className="text-secondary">
            {searchQuery
              ? 'Try adjusting your search query.'
              : 'Upload your first document to get started with AI analysis.'}
          </p>
        </div>
      ) : (
        <div className="docs-grid">
          {filteredDocs.map((doc) => {
            const IconComp = DOC_TYPE_ICONS[doc.document_type] || FileText
            const statusInfo = STATUS_MAP[doc.status] || STATUS_MAP.uploaded
            const embeddingInfo = EMBEDDING_MAP[doc.embedding_status] || EMBEDDING_MAP.pending
            const StatusIcon = statusInfo.icon

            return (
              <Link
                to={`/document/${doc.id}`}
                className="doc-card"
                key={doc.id}
                id={`doc-card-${doc.id}`}
              >
                <div className="doc-card-header">
                  <div className={`doc-card-icon ${doc.document_type}`}>
                    <IconComp size={22} />
                  </div>
                  <div className="doc-card-title-group">
                    <div className="doc-card-title">{doc.original_filename}</div>
                    <div className="doc-card-type">{doc.document_type}</div>
                  </div>
                </div>

                <div className="doc-card-meta">
                  <span className="doc-card-meta-item">
                    <HardDrive size={12} />
                    {formatBytes(doc.file_size)}
                  </span>
                  <span className="doc-card-meta-item">
                    <Clock size={12} />
                    {formatDate(doc.created_at)}
                  </span>
                  {doc.has_ocr && (
                    <span className="badge badge-info" style={{ fontSize: '10px', padding: '1px 6px' }}>
                      OCR
                    </span>
                  )}
                </div>

                <div className="doc-card-footer">
                  <div className="doc-card-status">
                    <span className={`badge ${statusInfo.class}`}>
                      <StatusIcon size={10} />
                      {statusInfo.label}
                    </span>
                    <span className={`badge ${embeddingInfo.class}`}>
                      {embeddingInfo.label}
                    </span>
                  </div>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={(e) => handleDelete(e, doc.id)}
                    data-tooltip="Delete"
                    id={`delete-doc-${doc.id}`}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
