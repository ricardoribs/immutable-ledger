import axios from 'axios';

// Cria a instancia do Axios apontando para o Docker local.
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
});

// Interceptor: adiciona o token automaticamente em toda requisicao.
api.interceptors.request.use((config) => {
  const storage = localStorage.getItem('luisbank-auth');
  if (storage) {
    try {
      const { state } = JSON.parse(storage);
      if (state.token) {
        config.headers.Authorization = `Bearer ${state.token}`;
      }
    } catch (e) {
      console.error('Erro ao ler token do storage', e);
    }
  }
  return config;
});

export default api;
