import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Define o formato do Usuário que vem do Backend
interface User {
  id: number;
  name: string;
  email: string | null;
  cpf_masked: string;
  mfa_enabled: boolean;
}

// Define o formato do Estado Global de Auth
interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  
  // Ações que podem ser chamadas
  setLogin: (token: string, refresh: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      // Estado Inicial
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      // Função de Login (Salva tokens e marca como autenticado)
      setLogin: (token, refresh) => set({ 
        token, 
        refreshToken: refresh, 
        isAuthenticated: true 
      }),
      
      // Atualiza dados do usuário (ex: após chamada /me)
      setUser: (user) => set({ user }),
      
      // Logout (Limpa tudo)
      logout: () => {
        set({ 
          token: null, 
          refreshToken: null, 
          user: null, 
          isAuthenticated: false 
        });
        // Opcional: Limpar localstorage forçadamente se o persist falhar
        localStorage.removeItem('luisbank-auth');
      },
    }),
    {
      name: 'luisbank-auth', // Nome da chave no LocalStorage do navegador
    }
  )
);