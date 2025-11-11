import axios from 'axios';
import { BASE_URL, API_BASE_URL } from './apiConfig';

// Use dynamic backend URL from apiConfig
const BACKEND_URL = BASE_URL;
const API_URL = API_BASE_URL;

console.log('🔧 API CONFIG (DYNAMIC):', {
  BACKEND_URL,
  API_URL
});

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 segundos de timeout
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle errors - NUNCA DESCONECTAR
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Apenas log, NUNCA redirecionar ou limpar token
    if (error.response?.status === 401) {
      console.warn('⚠️ Erro 401 - Token pode estar inválido, mas mantendo sessão');
    }
    return Promise.reject(error);
  }
);

export default api;

// WebSocket connection
export const createWebSocket = (userId) => {
  // CORREÇÃO CRÍTICA: Usar wss:// para HTTPS e ws:// para HTTP
  const wsUrl = API_URL.replace(/^https?/, (match) => match === 'https' ? 'wss' : 'ws');
  // Gera session ID único
  let sessionId = localStorage.getItem('session_id');
  if (!sessionId) {
    sessionId = Date.now().toString() + Math.random().toString(36);
    localStorage.setItem('session_id', sessionId);
  }
  console.log('🔌 Conectando WebSocket:', `${wsUrl}/ws/${userId}/${sessionId}`);
  return new WebSocket(`${wsUrl}/ws/${userId}/${sessionId}`);
};
