import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Accept': 'application/json',
  },
});

export const documentApi = {
  async uploadDocument(file, documentType, onUploadProgress) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    const response = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(percent);
        }
      },
    });
    return response.data;
  },

  async fetchDocuments() {
    const response = await apiClient.get('/documents');
    return response.data;
  },

  async fetchDocumentDetails(id) {
    const response = await apiClient.get(`/documents/${id}`);
    return response.data;
  },

  async reprocessDocument(id) {
    const response = await apiClient.post(`/documents/${id}/process`);
    return response.data;
  },

  async reindexDocument(id) {
    const response = await apiClient.post(`/documents/${id}/index`);
    return response.data;
  },

  async fetchIndexStatus(id) {
    const response = await apiClient.get(`/documents/${id}/index-status`);
    return response.data;
  },

  async searchDocument(id, query, topK = 5) {
    const response = await apiClient.post(`/documents/${id}/search`, {
      query,
      top_k: topK,
    });
    return response.data;
  },

  async askDocument(id, question, topK = 5) {
    const response = await apiClient.post(`/documents/${id}/ask`, {
      question,
      top_k: topK,
    });
    return response.data;
  },

  async analyzeDocument(id, forceRefresh = false) {
    const response = await apiClient.post(`/documents/${id}/analyze`, {
      force_refresh: forceRefresh,
    });
    return response.data;
  },

  async fetchDocumentAnalysis(id) {
    const response = await apiClient.get(`/documents/${id}/analysis`);
    return response.data;
  },

  async fetchDocumentChunks(id) {
    const response = await apiClient.get(`/documents/${id}/chunks`);
    return response.data;
  },

  async deleteDocument(id) {
    const response = await apiClient.delete(`/documents/${id}`);
    return response.data;
  },
};
