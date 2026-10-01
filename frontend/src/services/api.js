import axios from 'axios';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Documents ───
export const uploadDocument = async (file, documentType) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);
  const { data } = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const listDocuments = async () => {
  const { data } = await api.get('/documents');
  return data;
};

export const getDocument = async (id) => {
  const { data } = await api.get(`/documents/${id}`);
  return data;
};

export const deleteDocument = async (id) => {
  const { data } = await api.delete(`/documents/${id}`);
  return data;
};

export const processDocument = async (id) => {
  const { data } = await api.post(`/documents/${id}/process`);
  return data;
};

export const reindexDocument = async (id) => {
  const { data } = await api.post(`/documents/${id}/index`);
  return data;
};

export const getIndexStatus = async (id) => {
  const { data } = await api.get(`/documents/${id}/index-status`);
  return data;
};

export const getDocumentChunks = async (id) => {
  const { data } = await api.get(`/documents/${id}/chunks`);
  return data;
};

// ─── RAG Q&A ───
export const askDocument = async (id, question, persona = 'consumer', topK = null) => {
  const payload = { question, persona };
  if (topK) payload.top_k = topK;
  const { data } = await api.post(`/documents/${id}/ask`, payload);
  return data;
};

export const reexplainDocument = async (id, question, persona, sourceChunkIds = null) => {
  const payload = { question, persona };
  if (sourceChunkIds) payload.source_chunk_ids = sourceChunkIds;
  const { data } = await api.post(`/documents/${id}/explain`, payload);
  return data;
};

// ─── Analysis ───
export const analyzeDocument = async (id, persona = 'consumer', forceRefresh = false) => {
  const { data } = await api.post(`/documents/${id}/analyze`, {
    persona,
    force_refresh: forceRefresh,
  });
  return data;
};

export const getDocumentAnalysis = async (id, persona = 'consumer') => {
  const { data } = await api.get(`/documents/${id}/analysis`, {
    params: { persona },
  });
  return data;
};

// ─── Suggested Questions ───
export const generateSuggestedQuestions = async (id, persona = 'consumer', forceRefresh = false) => {
  const { data } = await api.post(`/documents/${id}/suggested-questions`, {
    persona,
    force_refresh: forceRefresh,
  });
  return data;
};

export const getSuggestedQuestions = async (id) => {
  const { data } = await api.get(`/documents/${id}/suggested-questions`);
  return data;
};

// ─── Conversations ───
export const createConversation = async (documentId, title = null, persona = 'consumer') => {
  const { data } = await api.post(`/documents/${documentId}/conversations`, {
    title,
    persona,
  });
  return data;
};

export const sendMessage = async (conversationId, content, persona = null) => {
  const payload = { content };
  if (persona) payload.persona = persona;
  const { data } = await api.post(`/conversations/${conversationId}/messages`, payload);
  return data;
};

export const getConversation = async (conversationId) => {
  const { data } = await api.get(`/conversations/${conversationId}`);
  return data;
};

// ─── Search ───
export const searchDocument = async (id, query, topK = 5) => {
  const { data } = await api.post(`/documents/${id}/search`, {
    query,
    top_k: topK,
  });
  return data;
};

export default api;
