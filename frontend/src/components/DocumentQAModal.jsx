import React, { useState, useEffect, useRef } from 'react';
import { X, Sparkles, Send, Loader2, BookOpen, AlertTriangle, CheckCircle2, Info, MessageSquare, HelpCircle, RefreshCw } from 'lucide-react';
import { documentApi } from '../services/documentApi';
import PersonaSelector, { PERSONAS } from './PersonaSelector';

export default function DocumentQAModal({ document, onClose, initialQuestion = null }) {
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [selectedPersona, setSelectedPersona] = useState('consumer');
  const [reexplainingId, setReexplainingId] = useState(null);
  const [conversation, setConversation] = useState(null);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [error, setError] = useState(null);
  const chatEndRef = useRef(null);

  if (!document) return null;

  useEffect(() => {
    let isMounted = true;

    async function initSession() {
      try {
        const convData = await documentApi.createConversation(
          document.id,
          `Q&A - ${document.original_filename}`,
          selectedPersona
        );
        if (isMounted) {
          setConversation(convData);
        }

        setLoadingQuestions(true);
        try {
          const questionsData = await documentApi.generateSuggestedQuestions(document.id, false);
          if (isMounted && questionsData?.questions) {
            setSuggestedQuestions(questionsData.questions);
          }
        } catch (qErr) {
          console.warn("Could not fetch suggested questions:", qErr);
        } finally {
          if (isMounted) setLoadingQuestions(false);
        }

        if (initialQuestion && isMounted) {
          handleSendMessage(convData.id, initialQuestion, selectedPersona);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.response?.data?.detail || "Failed to initialize Q&A session.");
        }
      }
    }

    initSession();

    return () => {
      isMounted = false;
    };
  }, [document.id]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation?.messages, asking]);

  const handleSendMessage = async (convIdOverride = null, customText = null, personaOverride = null) => {
    const textToSend = customText || question;
    const activeConvId = convIdOverride || conversation?.id;
    const personaToUse = personaOverride || selectedPersona;

    if (!textToSend.trim() || !activeConvId || asking) return;

    if (!customText) {
      setQuestion('');
    }

    setAsking(true);
    setError(null);

    const tempUserMsg = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: textToSend.trim(),
      persona: personaToUse,
      created_at: new Date().toISOString(),
    };

    setConversation((prev) => ({
      ...prev,
      persona: personaToUse,
      messages: [...(prev?.messages || []), tempUserMsg],
    }));

    try {
      await documentApi.sendConversationMessage(activeConvId, textToSend.trim(), personaToUse);
      const updatedConv = await documentApi.fetchConversation(activeConvId);
      setConversation(updatedConv);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to generate answer from document.");
      if (activeConvId) {
        try {
          const freshConv = await documentApi.fetchConversation(activeConvId);
          setConversation(freshConv);
        } catch (_) {}
      }
    } finally {
      setAsking(false);
    }
  };

  const handleReexplain = async (msgId, userQuestionText, targetPersona, citations = []) => {
    if (!conversation?.id || asking) return;

    setReexplainingId(msgId);
    setError(null);

    const sourceChunkIds = citations.map((c) => c.chunk_id).filter(Boolean);

    try {
      // Re-explain existing evidence in new persona
      const reexplainResp = await documentApi.reexplainDocument(
        document.id,
        userQuestionText,
        targetPersona,
        sourceChunkIds
      );

      // Append user re-explain message and assistant response to conversation session
      await documentApi.sendConversationMessage(
        conversation.id,
        `[Re-explained in ${targetPersona.toUpperCase()} mode] ${userQuestionText}`,
        targetPersona
      );

      const updatedConv = await documentApi.fetchConversation(conversation.id);
      setConversation(updatedConv);
      setSelectedPersona(targetPersona);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to re-explain answer.");
    } finally {
      setReexplainingId(null);
    }
  };

  const getConfidenceBadge = (confidence) => {
    switch (confidence?.toLowerCase()) {
      case 'high':
        return (
          <span className="px-2.5 py-0.5 bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 rounded-full text-[11px] font-semibold flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> High Grounded
          </span>
        );
      case 'medium':
        return (
          <span className="px-2.5 py-0.5 bg-amber-500/15 text-amber-400 border border-amber-500/30 rounded-full text-[11px] font-semibold flex items-center gap-1">
            <Info className="w-3 h-3" /> Medium Confidence
          </span>
        );
      case 'low':
      default:
        return (
          <span className="px-2.5 py-0.5 bg-rose-500/15 text-rose-400 border border-rose-500/30 rounded-full text-[11px] font-semibold flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> Low Confidence
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
                <span className="text-xs font-semibold px-2.5 py-0.5 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full capitalize">
                  {selectedPersona} Persona
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

        {/* Chat Transcript Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold">Error</h4>
                <p className="mt-0.5 text-xs text-rose-300">{error}</p>
              </div>
            </div>
          )}

          {(!conversation?.messages || conversation.messages.length === 0) && !asking && (
            <div className="flex flex-col items-center justify-center h-full text-center p-12 text-slate-500 space-y-3">
              <div className="p-4 bg-slate-900/60 rounded-2xl border border-slate-800 text-slate-400">
                <MessageSquare className="w-8 h-8 text-purple-400/80" />
              </div>
              <h4 className="text-base font-semibold text-slate-300">Start Persona-Adapted Grounded Conversation</h4>
              <p className="text-xs text-slate-400 max-w-md leading-relaxed">
                Choose an explanation persona below (Consumer, Professional, Business), then ask any question or click a suggested question chip.
              </p>
            </div>
          )}

          {conversation?.messages?.map((msg, idx) => {
            const isUser = msg.role === 'user';
            const msgPersona = msg.persona || selectedPersona;
            const personaMeta = PERSONAS.find((p) => p.id === msgPersona) || PERSONAS[0];

            return (
              <div key={msg.id || idx} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                {isUser ? (
                  <div className="max-w-[80%] p-4 bg-purple-600 text-white rounded-2xl rounded-tr-none text-sm shadow-md font-sans leading-relaxed">
                    {msg.content}
                  </div>
                ) : (
                  <div className="max-w-[90%] w-full p-6 bg-slate-900/70 border border-slate-800 rounded-2xl rounded-tl-none space-y-4 shadow-lg">
                    <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-purple-400" />
                        <h4 className="text-xs font-bold text-slate-200">Doc Clarity AI</h4>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${personaMeta.badgeClass}`}>
                          {personaMeta.name}
                        </span>
                      </div>
                      {getConfidenceBadge(msg.confidence)}
                    </div>

                    <div className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap font-sans">
                      {msg.content}
                    </div>

                    {/* Re-explain Actions */}
                    <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/60">
                      <span className="text-[11px] text-slate-400 font-semibold">Re-explain as:</span>
                      {PERSONAS.map((p) => {
                        if (p.id === msgPersona) return null;
                        return (
                          <button
                            key={p.id}
                            disabled={asking || reexplainingId === msg.id}
                            onClick={() => {
                              const prevUserMsg = conversation?.messages?.[idx - 1];
                              const questionText = prevUserMsg?.content || "Previous topic";
                              handleReexplain(msg.id, questionText, p.id, msg.citations);
                            }}
                            className="text-[11px] px-2.5 py-1 bg-slate-800 hover:bg-slate-700/80 text-slate-300 hover:text-purple-300 rounded-lg border border-slate-700/60 transition-all flex items-center gap-1 disabled:opacity-50"
                          >
                            {reexplainingId === msg.id ? (
                              <Loader2 className="w-3 h-3 animate-spin text-purple-400" />
                            ) : (
                              <RefreshCw className="w-3 h-3 text-slate-400" />
                            )}
                            Explain as {p.name}
                          </button>
                        );
                      })}
                    </div>

                    {/* Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="pt-3 border-t border-slate-800/60 space-y-2">
                        <h5 className="text-xs font-bold text-slate-400 flex items-center gap-1.5">
                          <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                          Source Citations ({msg.citations.length})
                        </h5>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {msg.citations.map((c, cIdx) => (
                            <div key={cIdx} className="p-3 bg-slate-950/60 border border-slate-800 rounded-xl text-xs space-y-1">
                              <div className="flex items-center justify-between text-slate-300 font-semibold">
                                <span>Source #{cIdx + 1}</span>
                                <span className="text-purple-400 font-mono font-bold text-[10px]">
                                  {(c.relevance_score * 100).toFixed(0)}% match
                                </span>
                              </div>
                              <div className="text-[11px] text-slate-400 flex items-center gap-2">
                                {c.page_number && <span>Page {c.page_number}</span>}
                                {c.section && <span>• {c.section}</span>}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}

          {asking && (
            <div className="flex items-start gap-3">
              <div className="p-4 bg-slate-900/70 border border-slate-800 rounded-2xl rounded-tl-none flex items-center gap-3 text-xs text-slate-300">
                <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
                <span>Generating {selectedPersona.toUpperCase()} persona answer...</span>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input & Persona Selector Panel */}
        <div className="p-6 bg-slate-900/60 border-t border-slate-800 shrink-0 space-y-4">
          <PersonaSelector selectedPersona={selectedPersona} onChange={setSelectedPersona} />

          {/* Suggested Questions */}
          <div className="space-y-2 pt-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-400">
              <HelpCircle className="w-3.5 h-3.5 text-purple-400" />
              <span>Suggested Questions:</span>
              {loadingQuestions && <Loader2 className="w-3 h-3 animate-spin text-purple-400" />}
            </div>

            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.map((q) => (
                <button
                  key={q.id}
                  onClick={() => handleSendMessage(null, q.question, selectedPersona)}
                  disabled={asking}
                  className="text-xs bg-slate-800/80 hover:bg-slate-700 text-slate-200 hover:text-purple-300 px-3 py-1.5 rounded-xl border border-slate-700/60 transition-all text-left max-w-sm truncate"
                >
                  <span className="font-semibold text-purple-400 mr-1.5 capitalize">[{q.category}]</span>
                  {q.question}
                </button>
              ))}
            </div>
          </div>

          {/* Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex gap-3"
          >
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={`Ask a question in ${selectedPersona.toUpperCase()} mode...`}
              className="flex-1 bg-slate-950/80 border border-slate-700/80 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
            />

            <button
              type="submit"
              disabled={!question.trim() || asking}
              className={`py-3 px-6 rounded-xl font-semibold text-sm transition-all duration-200 flex items-center gap-2 shrink-0 ${
                !question.trim() || asking
                  ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                  : 'bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-600/30'
              }`}
            >
              {asking ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Thinking...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Send</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
