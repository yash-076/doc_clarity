import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import {
  FileText,
  Scale,
  Shield,
  Heart,
  Clock,
  HardDrive,
  CheckCircle,
  AlertCircle,
  ArrowLeft,
  Send,
  Search,
  BarChart3,
  MessageSquare,
  Sparkles,
  RefreshCw,
  Loader,
  BookOpen,
  Calendar,
  DollarSign,
  AlertTriangle,
  XCircle,
  Users,
  Lightbulb,
  Zap,
  ChevronRight,
  User,
  Bot,
} from 'lucide-react'
import {
  getDocument,
  analyzeDocument,
  getDocumentAnalysis,
  askDocument,
  searchDocument,
  generateSuggestedQuestions,
  getSuggestedQuestions,
  createConversation,
  sendMessage,
  getConversation,
} from '../services/api'
import './DocumentPage.css'

const DOC_TYPE_ICONS = { legal: Scale, insurance: Shield, medical: Heart, other: FileText }

const PERSONA_OPTIONS = [
  { value: 'consumer', name: 'Consumer', desc: 'Simple, plain English' },
  { value: 'professional', name: 'Professional', desc: 'Technical precision' },
  { value: 'business', name: 'Business', desc: 'Operational focus' },
]

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function DocumentPage() {
  const { id } = useParams()
  const chatEndRef = useRef(null)

  // State
  const [document, setDocument] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('analysis')
  const [persona, setPersona] = useState('consumer')
  const [error, setError] = useState(null)

  // Analysis state
  const [analysis, setAnalysis] = useState(null)
  const [analysisLoading, setAnalysisLoading] = useState(false)

  // Q&A state
  const [suggestedQuestions, setSuggestedQuestions] = useState([])
  const [conversation, setConversation] = useState(null)
  const [messages, setMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)

  // Search state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchLoading, setSearchLoading] = useState(false)

  // Load document
  useEffect(() => {
    async function load() {
      try {
        setLoading(true)
        const doc = await getDocument(id)
        setDocument(doc)
      } catch (err) {
        setError('Failed to load document details.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  // Load analysis when tab/persona changes
  useEffect(() => {
    if (activeTab === 'analysis' && document && document.status === 'completed') {
      loadAnalysis()
    }
  }, [activeTab, persona, document?.id])

  // Load suggested questions for Q&A tab
  useEffect(() => {
    if (activeTab === 'qa' && document && document.status === 'completed') {
      loadSuggestedQuestions()
    }
  }, [activeTab, document?.id])

  const loadAnalysis = async (forceRefresh = false) => {
    try {
      setAnalysisLoading(true)
      let data
      if (forceRefresh) {
        data = await analyzeDocument(id, persona, true)
      } else {
        try {
          data = await getDocumentAnalysis(id, persona)
        } catch {
          data = await analyzeDocument(id, persona, false)
        }
      }
      setAnalysis(data)
    } catch (err) {
      // Analysis might not exist yet — that's fine
      setAnalysis(null)
    } finally {
      setAnalysisLoading(false)
    }
  }

  const loadSuggestedQuestions = async () => {
    try {
      let data
      try {
        data = await getSuggestedQuestions(id)
      } catch {
        data = await generateSuggestedQuestions(id, persona)
      }
      setSuggestedQuestions(data.questions || [])
    } catch {
      setSuggestedQuestions([])
    }
  }

  // Chat
  const handleAskQuestion = async (question) => {
    if (!question.trim()) return

    const userMsg = { role: 'user', content: question }
    setMessages((prev) => [...prev, userMsg])
    setChatInput('')
    setChatLoading(true)

    try {
      let response

      if (conversation) {
        // Multi-turn: send message to conversation
        response = await sendMessage(conversation.id, question, persona)
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: response.content,
          citations: response.citations,
          confidence: response.confidence,
          persona: response.persona,
        }])
      } else {
        // First question: create conversation then ask
        const conv = await createConversation(id, null, persona)
        setConversation(conv)

        response = await sendMessage(conv.id, question, persona)
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: response.content,
          citations: response.citations,
          confidence: response.confidence,
          persona: response.persona,
        }])
      }
    } catch (err) {
      // Fallback: use direct ask endpoint
      try {
        const response = await askDocument(id, question, persona)
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: response.answer,
          citations: response.citations,
          confidence: response.confidence,
          persona: response.persona,
          disclaimer: response.disclaimer,
        }])
      } catch (askErr) {
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: 'Sorry, I encountered an error processing your question. Please try again.',
          confidence: 'low',
        }])
      }
    } finally {
      setChatLoading(false)
    }
  }

  // Search
  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    try {
      setSearchLoading(true)
      const data = await searchDocument(id, searchQuery)
      setSearchResults(data.results || [])
    } catch {
      setSearchResults([])
    } finally {
      setSearchLoading(false)
    }
  }

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner spinner-lg" />
        <p className="text-secondary">Loading document...</p>
      </div>
    )
  }

  if (error || !document) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">
          <AlertCircle size={36} />
        </div>
        <h3>Document Not Found</h3>
        <p className="text-secondary">{error || 'The document could not be loaded.'}</p>
        <Link to="/dashboard" className="btn btn-primary">
          <ArrowLeft size={16} /> Back to Dashboard
        </Link>
      </div>
    )
  }

  const IconComp = DOC_TYPE_ICONS[document.document_type] || FileText

  return (
    <div className="doc-page animate-fadeIn">
      {/* ─── Left Panel ─── */}
      <div className="doc-info-panel">
        <div className="doc-info-card">
          <div className="doc-info-header">
            <div className={`doc-info-icon ${document.document_type}`}>
              <IconComp size={28} />
            </div>
            <div>
              <div className="doc-info-title">{document.original_filename}</div>
              <div className="doc-info-type">{document.document_type}</div>
            </div>
          </div>

          <div className="doc-info-details">
            <div className="doc-info-row">
              <span className="doc-info-row-label"><HardDrive size={14} /> Size</span>
              <span className="doc-info-row-value">{formatBytes(document.file_size)}</span>
            </div>
            <div className="doc-info-row">
              <span className="doc-info-row-label"><Clock size={14} /> Created</span>
              <span className="doc-info-row-value">{formatDate(document.created_at)}</span>
            </div>
            <div className="doc-info-row">
              <span className="doc-info-row-label"><CheckCircle size={14} /> Status</span>
              <span className={`badge ${document.status === 'completed' ? 'badge-success' : 'badge-warning'}`}>
                {document.status}
              </span>
            </div>
            <div className="doc-info-row">
              <span className="doc-info-row-label"><BarChart3 size={14} /> AI Status</span>
              <span className={`badge ${document.embedding_status === 'indexed' ? 'badge-success' : 'badge-warning'}`}>
                {document.embedding_status === 'indexed' ? 'Ready' : document.embedding_status === 'pending' ? 'Preparing' : 'Not Ready'}
              </span>
            </div>
            {document.has_ocr && (
              <div className="doc-info-row">
                <span className="doc-info-row-label"><BookOpen size={14} /> OCR</span>
                <span className="badge badge-info">Enabled</span>
              </div>
            )}
          </div>

          <div className="doc-info-actions">
            <Link to="/dashboard" className="btn btn-secondary btn-sm">
              <ArrowLeft size={14} /> Back to Dashboard
            </Link>
          </div>
        </div>

        {/* Persona Selector */}
        <div className="persona-selector">
          <div className="persona-selector-label">Explanation Mode</div>
          <div className="persona-options">
            {PERSONA_OPTIONS.map((p) => (
              <button
                key={p.value}
                className={`persona-option ${persona === p.value ? 'active' : ''}`}
                onClick={() => setPersona(p.value)}
                id={`persona-${p.value}`}
              >
                <span className="persona-option-dot" />
                <div className="persona-option-info">
                  <div className="persona-option-name">{p.name}</div>
                  <div className="persona-option-desc">{p.desc}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ─── Right Panel ─── */}
      <div className="doc-main-panel">
        {/* Tab Bar */}
        <div className="doc-tabs" id="doc-tab-bar">
          <button
            className={`doc-tab ${activeTab === 'analysis' ? 'active' : ''}`}
            onClick={() => setActiveTab('analysis')}
            id="tab-analysis"
          >
            <BarChart3 size={16} /> Analysis
          </button>
          <button
            className={`doc-tab ${activeTab === 'qa' ? 'active' : ''}`}
            onClick={() => setActiveTab('qa')}
            id="tab-qa"
          >
            <MessageSquare size={16} /> Ask AI
          </button>
          <button
            className={`doc-tab ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => setActiveTab('search')}
            id="tab-search"
          >
            <Search size={16} /> Search
          </button>
        </div>

        {/* ─── Analysis Tab ─── */}
        {activeTab === 'analysis' && (
          <div className="analysis-section">
            {document.status !== 'completed' ? (
              <div className="empty-state">
                <div className="empty-state-icon">
                  <Loader size={36} />
                </div>
                <h3>Document Still Processing</h3>
                <p className="text-secondary">
                  Analysis will be available after processing completes.
                </p>
              </div>
            ) : analysisLoading ? (
              <div className="analysis-loading">
                <div className="analysis-loading-block skeleton" />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
                  <div className="analysis-loading-block skeleton" />
                  <div className="analysis-loading-block skeleton" />
                  <div className="analysis-loading-block skeleton" />
                  <div className="analysis-loading-block skeleton" />
                </div>
              </div>
            ) : analysis ? (
              <>
                {/* Summary */}
                <div className="analysis-summary">
                  <div className="analysis-summary-header">
                    <h3 className="analysis-summary-title">
                      <Sparkles size={20} style={{ color: 'var(--color-primary-400)' }} />
                      Executive Summary
                    </h3>
                    <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
                      <span className={`confidence-indicator ${analysis.confidence}`}>
                        <span className={`confidence-dot ${analysis.confidence}`} />
                        {analysis.confidence} confidence
                      </span>
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => loadAnalysis(true)}
                        data-tooltip="Refresh Analysis"
                        id="refresh-analysis-btn"
                      >
                        <RefreshCw size={14} />
                      </button>
                    </div>
                  </div>
                  <div className="analysis-summary-text markdown-content">
                    <ReactMarkdown>{analysis.summary}</ReactMarkdown>
                  </div>
                </div>

                {/* Analysis Blocks Grid */}
                <div className="analysis-grid">
                  {/* Key Points */}
                  {analysis.key_points?.length > 0 && (
                    <div className="analysis-block">
                      <div className="analysis-block-header">
                        <div className="analysis-block-icon green"><Lightbulb size={16} /></div>
                        <span className="analysis-block-title">Key Points</span>
                        <span className="analysis-block-count">{analysis.key_points.length}</span>
                      </div>
                      <div className="analysis-items">
                        {analysis.key_points.map((kp, i) => (
                          <div className="analysis-item" key={i}>
                            <div className="analysis-item-title">{kp.title}</div>
                            <div className="analysis-item-desc">{kp.description}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Important Dates */}
                  {analysis.important_dates?.length > 0 && (
                    <div className="analysis-block">
                      <div className="analysis-block-header">
                        <div className="analysis-block-icon blue"><Calendar size={16} /></div>
                        <span className="analysis-block-title">Important Dates</span>
                        <span className="analysis-block-count">{analysis.important_dates.length}</span>
                      </div>
                      <div className="analysis-items">
                        {analysis.important_dates.map((d, i) => (
                          <div className="analysis-item" key={i}>
                            <div className="analysis-item-title">{d.description}</div>
                            {d.date && <div className="analysis-item-desc">{d.date}</div>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Financial Terms */}
                  {analysis.financial_terms?.length > 0 && (
                    <div className="analysis-block">
                      <div className="analysis-block-header">
                        <div className="analysis-block-icon yellow"><DollarSign size={16} /></div>
                        <span className="analysis-block-title">Financial Terms</span>
                        <span className="analysis-block-count">{analysis.financial_terms.length}</span>
                      </div>
                      <div className="analysis-items">
                        {analysis.financial_terms.map((f, i) => (
                          <div className="analysis-item" key={i}>
                            <div className="analysis-item-title">{f.description}</div>
                            {f.amount && <div className="analysis-item-desc">{f.amount}</div>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Obligations */}
                  {analysis.obligations?.length > 0 && (
                    <div className="analysis-block">
                      <div className="analysis-block-header">
                        <div className="analysis-block-icon purple"><Users size={16} /></div>
                        <span className="analysis-block-title">Obligations</span>
                        <span className="analysis-block-count">{analysis.obligations.length}</span>
                      </div>
                      <div className="analysis-items">
                        {analysis.obligations.map((o, i) => (
                          <div className="analysis-item" key={i}>
                            <div className="analysis-item-title">{o.party}</div>
                            <div className="analysis-item-desc">{o.description}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Exclusions */}
                  {analysis.exclusions?.length > 0 && (
                    <div className="analysis-block">
                      <div className="analysis-block-header">
                        <div className="analysis-block-icon red"><XCircle size={16} /></div>
                        <span className="analysis-block-title">Exclusions</span>
                        <span className="analysis-block-count">{analysis.exclusions.length}</span>
                      </div>
                      <div className="analysis-items">
                        {analysis.exclusions.map((e, i) => (
                          <div className="analysis-item" key={i}>
                            <div className="analysis-item-desc">{e.description}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Attention Items */}
                  {analysis.attention_items?.length > 0 && (
                    <div className="analysis-block">
                      <div className="analysis-block-header">
                        <div className="analysis-block-icon red"><AlertTriangle size={16} /></div>
                        <span className="analysis-block-title">Attention Required</span>
                        <span className="analysis-block-count">{analysis.attention_items.length}</span>
                      </div>
                      <div className="analysis-items">
                        {analysis.attention_items.map((a, i) => (
                          <div className={`analysis-item attention-item ${a.severity}`} key={i}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: '4px' }}>
                              <div className="analysis-item-title" style={{ flex: 1 }}>{a.title}</div>
                              <span className={`badge ${a.severity === 'high' ? 'badge-error' : a.severity === 'medium' ? 'badge-warning' : 'badge-info'}`}>
                                {a.severity}
                              </span>
                            </div>
                            <div className="analysis-item-desc">{a.description}</div>
                            <div className="analysis-item-meta">
                              <span className="badge badge-neutral">{a.category}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="empty-state">
                <div className="empty-state-icon">
                  <BarChart3 size={36} />
                </div>
                <h3>No Analysis Yet</h3>
                <p className="text-secondary">
                  Generate an AI-powered analysis of this document.
                </p>
                <button
                  className="btn btn-primary"
                  onClick={() => loadAnalysis(true)}
                  id="generate-analysis-btn"
                >
                  <Sparkles size={16} /> Generate Analysis
                </button>
              </div>
            )}
          </div>
        )}

        {/* ─── Q&A Tab ─── */}
        {activeTab === 'qa' && (
          <div className="qa-section">
            {/* Suggested Questions */}
            {suggestedQuestions.length > 0 && messages.length === 0 && (
              <div className="suggested-questions">
                <div className="suggested-questions-title">
                  <Lightbulb size={16} style={{ color: 'var(--color-primary-400)' }} />
                  Suggested Questions
                </div>
                <div className="suggested-questions-list">
                  {suggestedQuestions.map((q) => (
                    <button
                      className="suggested-question-btn"
                      key={q.id}
                      onClick={() => handleAskQuestion(q.question)}
                      id={`suggested-q-${q.id}`}
                    >
                      {q.question}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Chat Container */}
            <div className="chat-container" id="chat-container">
              <div className="chat-messages">
                {messages.length === 0 && (
                  <div className="empty-state" style={{ padding: 'var(--space-12) var(--space-6)' }}>
                    <div className="empty-state-icon">
                      <MessageSquare size={36} />
                    </div>
                    <h3>Ask a Question</h3>
                    <p className="text-secondary" style={{ maxWidth: '400px' }}>
                      Ask anything about this document. AI will provide grounded answers
                      with citations from the actual document content.
                    </p>
                  </div>
                )}

                {messages.map((msg, i) => (
                  <div className={`chat-message ${msg.role}`} key={i}>
                    <div className={`chat-avatar ${msg.role === 'user' ? 'user-avatar' : 'ai-avatar'}`}>
                      {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                    </div>
                    <div className="chat-bubble">
                      {msg.role === 'assistant' ? (
                        <div className="markdown-content">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                      ) : (
                        msg.content
                      )}

                      {msg.role === 'assistant' && (
                        <>
                          {msg.citations?.length > 0 && (
                            <div className="chat-citations">
                              {msg.citations.map((c, j) => (
                                <span className="chat-citation-tag" key={j}>
                                  {c.page_number ? `Page ${c.page_number}` : ''}
                                  {c.section ? ` · ${c.section}` : ''}
                                  {c.relevance_score ? ` (${(c.relevance_score * 100).toFixed(0)}%)` : ''}
                                </span>
                              ))}
                            </div>
                          )}
                          <div className="chat-bubble-meta">
                            {msg.confidence && (
                              <span className={`confidence-indicator ${msg.confidence}`}>
                                <span className={`confidence-dot ${msg.confidence}`} />
                                {msg.confidence}
                              </span>
                            )}
                            {msg.persona && (
                              <span style={{ textTransform: 'capitalize' }}>{msg.persona} mode</span>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                ))}

                {chatLoading && (
                  <div className="chat-message assistant">
                    <div className="chat-avatar ai-avatar">
                      <Bot size={16} />
                    </div>
                    <div className="chat-bubble" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      <span className="spinner" />
                      <span className="text-secondary">Analyzing document...</span>
                    </div>
                  </div>
                )}

                <div ref={chatEndRef} />
              </div>

              <div className="chat-input-container">
                <form
                  className="chat-input-wrapper"
                  onSubmit={(e) => {
                    e.preventDefault()
                    handleAskQuestion(chatInput)
                  }}
                >
                  <input
                    className="chat-input"
                    placeholder="Ask a question about this document..."
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    disabled={chatLoading}
                    id="chat-input"
                  />
                  <button
                    className="chat-send-btn"
                    type="submit"
                    disabled={chatLoading || !chatInput.trim()}
                    id="chat-send-btn"
                  >
                    <Send size={18} />
                  </button>
                </form>
              </div>
            </div>

            {messages.some((m) => m.disclaimer) && (
              <div className="disclaimer">
                {messages.find((m) => m.disclaimer)?.disclaimer}
              </div>
            )}
          </div>
        )}

        {/* ─── Search Tab ─── */}
        {activeTab === 'search' && (
          <div className="search-section">
            <form
              className="search-bar-container"
              onSubmit={(e) => {
                e.preventDefault()
                handleSearch()
              }}
            >
              <input
                className="input"
                placeholder="Search within this document..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                id="semantic-search-input"
              />
              <button
                className="btn btn-primary"
                type="submit"
                disabled={searchLoading || !searchQuery.trim()}
                id="semantic-search-btn"
              >
                {searchLoading ? <span className="spinner" /> : <Search size={16} />}
                Search
              </button>
            </form>

            {searchResults.length > 0 ? (
              <div className="search-results">
                {searchResults.map((r, i) => (
                  <div className="search-result-card" key={i}>
                    <div className="search-result-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        <span className="badge badge-neutral">Result {r.chunk_index ?? i + 1}</span>
                        {r.page_number && (
                          <span className="badge badge-neutral">Page {r.page_number}</span>
                        )}
                      </div>
                      <span
                        className="search-result-score"
                        style={{
                          color: r.score >= 0.7 ? 'var(--color-confidence-high)' :
                                 r.score >= 0.4 ? 'var(--color-confidence-medium)' :
                                 'var(--color-confidence-low)'
                        }}
                      >
                        {(r.score * 100).toFixed(1)}% match
                      </span>
                    </div>
                    <div className="search-result-text">{r.content || r.text}</div>
                  </div>
                ))}
              </div>
            ) : searchQuery && !searchLoading ? (
              <div className="empty-state">
                <div className="empty-state-icon">
                  <Search size={36} />
                </div>
                <h3>No Results Found</h3>
                <p className="text-secondary">Try different search terms.</p>
              </div>
            ) : !searchQuery ? (
              <div className="empty-state">
                <div className="empty-state-icon">
                  <Search size={36} />
                </div>
                <h3>Semantic Search</h3>
                <p className="text-secondary" style={{ maxWidth: '400px' }}>
                  Search within this document using natural language.
                  Results are ranked by semantic similarity.
                </p>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  )
}
