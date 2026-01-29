import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import api from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { toast } from 'sonner'; // Biblioteca de alertas bonita
import { ShieldCheck, Lock } from 'lucide-react';

export default function Login() {
  const [step, setStep] = useState<'CREDENTIALS' | 'MFA'>('CREDENTIALS');
  const [tempCreds, setTempCreds] = useState({ username: '', password: '' });
  
  const { register, handleSubmit } = useForm();
  const setLogin = useAuthStore((s) => s.setLogin);
  const setUser = useAuthStore((s) => s.setUser);
  const navigate = useNavigate();

  const onSubmit = async (data: any) => {
    try {
      const formData = new FormData();
      formData.append('username', step === 'CREDENTIALS' ? data.username : tempCreds.username);
      formData.append('password', step === 'CREDENTIALS' ? data.password : tempCreds.password);

      // Se estiver no passo 2, adiciona o OTP
      const params = step === 'MFA' ? { otp: data.otp } : {};

      const res = await api.post('/auth/login', formData, { params });

      // Sucesso!
      setLogin(res.data.access_token, res.data.refresh_token);
      
      // Busca dados do usuário
      const me = await api.get('/accounts/me');
      setUser(me.data);
      
      toast.success('Bem-vindo ao LuisBank!');
      navigate('/dashboard');

    } catch (error: any) {
      // Captura o erro específico de MFA que criamos no backend
      if (error.response?.status === 401 && error.response?.data?.detail?.includes('MFA_REQUIRED')) {
        setTempCreds({ username: data.username, password: data.password });
        setStep('MFA');
        toast.info('Autenticação de dois fatores necessária.');
      } 
      else if (error.response?.status === 429) {
        toast.error('Muitas tentativas! Aguarde 1 minuto.');
      }
      else {
        toast.error('Credenciais inválidas.');
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border-t-4 border-green-600">
        <h1 className="text-2xl font-bold text-center mb-6 text-slate-800">
          LuisBank <span className="text-xs bg-yellow-200 px-2 rounded">Secure</span>
        </h1>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          
          {step === 'CREDENTIALS' && (
            <>
              <div>
                <label className="block text-sm font-medium text-slate-700">Email ou CPF</label>
                <input {...register('username')} className="w-full p-2 border rounded-lg mt-1" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700">Senha</label>
                <input type="password" {...register('password')} className="w-full p-2 border rounded-lg mt-1" />
              </div>
            </>
          )}

          {step === 'MFA' && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="bg-blue-50 p-4 rounded-lg mb-4 flex items-center gap-3">
                <ShieldCheck className="text-blue-600" size={24} />
                <p className="text-sm text-blue-800">
                  Sua conta é protegida. Digite o código do <strong>Google Authenticator</strong> ou um <strong>Código de Backup</strong>.
                </p>
              </div>
              <label className="block text-sm font-medium text-slate-700">Código 2FA</label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 text-gray-400" size={16} />
                <input 
                  {...register('otp')} 
                  placeholder="000000 ou Backup Code"
                  className="w-full p-2 pl-10 border rounded-lg mt-1 font-mono text-center tracking-widest text-lg" 
                  autoFocus
                />
              </div>
            </div>
          )}

          <button type="submit" className="w-full bg-green-700 hover:bg-green-800 text-white p-3 rounded-lg font-bold transition-all">
            {step === 'CREDENTIALS' ? 'Continuar' : 'Validar Acesso'}
          </button>
        </form>
      </div>
    </div>
  );
}