import { useState } from 'react';
import { useForm } from 'react-hook-form';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';
import { ShieldCheck, Lock, ArrowRight, AlertTriangle, BadgeCheck } from 'lucide-react';

export default function Login() {
  const [step, setStep] = useState<'CREDENTIALS' | 'MFA'>('CREDENTIALS');
  const [tempCreds, setTempCreds] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [registerMsg, setRegisterMsg] = useState('');

  const { register, handleSubmit, reset } = useForm();
  const setLogin = useAuthStore((s) => s.setLogin);
  const setUser = useAuthStore((s) => s.setUser);

  const onRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setRegisterMsg('');
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      name: String(form.get('name')),
      cpf: String(form.get('cpf')),
      email: String(form.get('email')),
      password: String(form.get('password')),
      account_type: String(form.get('account_type') || 'CHECKING'),
    };
    try {
      await api.post('/ledger/accounts', payload);
      setRegisterMsg('Conta criada. Agora faça login.');
      e.currentTarget.reset();
    } catch (error: any) {
      const detail = error.response?.data?.detail || 'Erro ao criar conta.';
      setRegisterMsg(String(detail));
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: any) => {
    setLoading(true);
    setErrorMsg('');

    try {
      const formData = new FormData();
      formData.append('username', step === 'CREDENTIALS' ? data.username : tempCreds.username);
      formData.append('password', step === 'CREDENTIALS' ? data.password : tempCreds.password);

      const params = step === 'MFA' ? { otp: data.otp } : {};

      const res = await api.post('/ledger/auth/login', formData, { params });
      setLogin(res.data.access_token, res.data.refresh_token);

      const me = await api.get('/ledger/accounts/me');
      setUser(me.data);

      window.location.href = '/app/dashboard';
    } catch (error: any) {
      if (error.response) {
        const status = error.response.status;
        const detail = error.response.data?.detail || '';

        if (status === 401 && (detail.includes('MFA_REQUIRED') || detail.includes('MFA'))) {
          setTempCreds({ username: data.username, password: data.password });
          setStep('MFA');
          reset({ otp: '' });
        } else if (status === 429) {
          setErrorMsg('Muitas tentativas. Aguarde 1 minuto.');
        } else if (status === 400) {
          setErrorMsg(detail || 'Credenciais inválidas.');
        } else if (status === 401) {
          setErrorMsg('Credenciais inválidas ou código incorreto.');
        } else {
          setErrorMsg('Erro no servidor. Tente novamente.');
        }
      } else {
        setErrorMsg('Sem conexão com o servidor (verifique se o Docker está rodando).');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen lb-hero-bg lb-diagonal text-white">
      <div className="relative z-10">
        <header className="bg-white/10 border-b border-white/10">
          <div className="max-w-6xl mx-auto px-6 py-3 flex flex-wrap items-center gap-4 justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center font-bold">LB</div>
              <div className="font-semibold">LuisBank</div>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <div className="hidden md:flex items-center gap-2 bg-white/10 px-3 py-1 rounded-full">
                <span>Agência</span>
                <input className="w-16 bg-transparent focus:outline-none" placeholder="0001" />
                <span>Conta</span>
                <input className="w-24 bg-transparent focus:outline-none" placeholder="000000-0" />
              </div>
              <button className="px-3 py-1 rounded-full bg-white text-brand-dark font-semibold">Acessar</button>
              <label className="flex items-center gap-2">
                <input type="checkbox" className="accent-brand-accent" />
                Lembrar-me
              </label>
            </div>
          </div>
        </header>

        <main className="max-w-6xl mx-auto px-6 py-12 grid grid-cols-1 lg:grid-cols-[1.2fr_0.8fr] gap-10">
          <section className="space-y-8">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 border border-white/20 text-sm">
                <BadgeCheck size={16} />
                Banco real, experiência digital
              </div>
              <h1 className="text-4xl md:text-5xl font-semibold leading-tight">
                Banco pela internet LuisBank
              </h1>
              <p className="text-white/80 max-w-xl">
                Operações bancárias completas com governança e segurança. Acesse saldos, pagamentos, Pix, investimentos e tudo em um só painel.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { title: 'Conta digital', text: 'Controle total do seu dinheiro.' },
                { title: 'Pix instantâneo', text: 'Transferências 24/7.' },
                { title: 'Cartões inteligentes', text: 'Limites e segurança.' },
              ].map((item) => (
                <div key={item.title} className="lb-glass rounded-2xl p-4 text-brand-ink">
                  <div className="text-sm font-semibold text-brand-dark">{item.title}</div>
                  <div className="text-xs text-slate-600 mt-2">{item.text}</div>
                </div>
              ))}
            </div>
          </section>

          <section className="space-y-6">
            <div className="lb-surface rounded-3xl p-8 text-slate-900">
              <div className="flex items-center gap-2 text-sm text-brand-dark mb-6">
                <Lock size={16} />
                Conexão segura
              </div>

              {errorMsg && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg flex items-center gap-2">
                  <AlertTriangle size={16} />
                  {errorMsg}
                </div>
              )}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                {step === 'CREDENTIALS' && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-600 mb-1">Email ou CPF</label>
                      <input
                        {...register('username')}
                        required
                        placeholder="seu@email.com"
                        className="w-full p-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand-primary outline-none"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-600 mb-1">Senha</label>
                      <input
                        type="password"
                        {...register('password')}
                        required
                        placeholder="Sua senha"
                        className="w-full p-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand-primary outline-none"
                      />
                    </div>
                  </div>
                )}

                {step === 'MFA' && (
                  <div className="space-y-4">
                    <div className="bg-emerald-50 p-4 rounded-lg flex gap-3">
                      <ShieldCheck className="text-emerald-700 shrink-0" size={22} />
                      <p className="text-sm text-emerald-900 leading-snug">
                        Conta protegida. Digite o código do Google Authenticator ou seu código de backup.
                      </p>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-slate-600 mb-1">Código de segurança</label>
                      <input
                        {...register('otp')}
                        autoFocus
                        placeholder="000000"
                        maxLength={6}
                        className="w-full p-3 text-center text-2xl font-mono tracking-[0.4em] border border-slate-200 rounded-lg focus:ring-2 focus:ring-brand-primary outline-none uppercase"
                      />
                    </div>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-brand-primary hover:bg-brand-dark text-white p-3 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all disabled:opacity-70"
                >
                  {loading ? 'Processando...' : (step === 'CREDENTIALS' ? 'Entrar' : 'Validar acesso')}
                  {!loading && <ArrowRight size={18} />}
                </button>

                {step === 'MFA' && (
                  <button
                    type="button"
                    onClick={() => { setStep('CREDENTIALS'); setErrorMsg(''); }}
                    className="w-full text-sm text-slate-500 hover:text-brand-primary mt-2"
                  >
                    Voltar para senha
                  </button>
                )}
              </form>
            </div>

            <div className="bg-white/90 rounded-2xl p-6 text-slate-900">
              <h2 className="text-lg font-semibold text-brand-dark">Abra sua conta</h2>
              {registerMsg && (
                <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm rounded-lg">
                  {registerMsg}
                </div>
              )}
              <form onSubmit={onRegister} className="mt-4 grid grid-cols-1 gap-3">
                <input name="name" required placeholder="Nome completo" className="w-full p-3 border border-slate-200 rounded-lg" />
                <input name="cpf" required placeholder="CPF" className="w-full p-3 border border-slate-200 rounded-lg" />
                <input name="email" type="email" required placeholder="Email" className="w-full p-3 border border-slate-200 rounded-lg" />
                <input name="password" type="password" required placeholder="Senha" className="w-full p-3 border border-slate-200 rounded-lg" />
                <select name="account_type" className="w-full p-3 border border-slate-200 rounded-lg">
                  <option value="CHECKING">Conta corrente</option>
                  <option value="SAVINGS">Poupança</option>
                  <option value="SALARY">Conta salário</option>
                  <option value="DIGITAL">Conta digital</option>
                  <option value="INVESTMENT">Conta investimento</option>
                </select>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-brand-dark text-white p-3 rounded-lg font-semibold disabled:opacity-70"
                >
                  Criar conta
                </button>
              </form>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

