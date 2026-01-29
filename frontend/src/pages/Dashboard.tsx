import { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import api from '../services/api';
import TransferModal from '../components/TransferModal';
import PixModal from '../components/PixModal';

import { format } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import { ArrowDownUp, BadgeCheck, CreditCard, Landmark, PiggyBank, ShieldCheck, Wallet } from 'lucide-react';

export default function Dashboard() {
  const user = useAuthStore((s) => s.user);

  const [balance, setBalance] = useState<number | null>(null);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showBalance, setShowBalance] = useState(true);
  const [isTransferOpen, setIsTransferOpen] = useState(false);
  const [isPixOpen, setIsPixOpen] = useState(false);
  const [integrity, setIntegrity] = useState<any>(null);
  const [integrityLoading, setIntegrityLoading] = useState(false);
  const navigate = useNavigate();

  const portfolio = [
    { label: 'Renda fixa', value: 46, color: 'bg-slate-900' },
    { label: 'Fundos', value: 28, color: 'bg-emerald-700' },
    { label: 'Previdência', value: 16, color: 'bg-amber-600' },
    { label: 'Ações', value: 10, color: 'bg-rose-600' },
  ];

  useEffect(() => {
    async function fetchData() {
      if (!user?.id) return;
      try {
        const resBal = await api.get(`/ledger/accounts/${user.id}/balance`);
        setBalance(resBal.data.balance);

        const resExt = await api.get(`/ledger/accounts/${user.id}/statement`);
        setTransactions(resExt.data.transactions || []);
      } catch (error) {
        console.error('Erro ao buscar dados', error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [user]);

  const formatCurrency = (val: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  async function checkIntegrity() {
    setIntegrityLoading(true);
    const res = await api.get('/ledger/integrity');
    setIntegrity(res.data);
    setIntegrityLoading(false);
  }

  return (
    <div className="space-y-6">
      <section className="lb-card lb-card-deep lb-gradient-card p-6 lb-animate-in">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div className="space-y-2">
            <div className="lb-label text-white/70">Visão geral da conta</div>
            <h1 className="text-3xl font-semibold text-white">Saldo disponível</h1>
            <div className="text-4xl lb-money text-white">
              {showBalance ? formatCurrency(balance || 0) : 'R$ ****'}
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs text-white/70">
              <span>Agência 0001 • Conta {user?.id ? String(user.id).padStart(4, '0') : '0000'}</span>
              <span className="lb-pill bg-white/10 border-white/20 text-white/80">Perfil executivo</span>
              <span className="lb-pill bg-white/10 border-white/20 text-white/80">Status: Operacional</span>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <button onClick={() => setShowBalance(!showBalance)} className="lb-action-btn lb-btn-ghost border-white/30 text-white/80">
              {showBalance ? 'Ocultar saldo' : 'Exibir saldo'}
            </button>
            <button onClick={() => navigate('/app/payments')} className="lb-action-btn lb-btn-secondary">
              Nova transferência
            </button>
            <button onClick={() => setIsPixOpen(true)} className="lb-action-btn lb-btn-primary">
              Pix imediato
            </button>
          </div>
        </div>
        <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="lb-card lb-card-info lb-card-compact bg-white/95">
            <div className="flex items-center justify-between">
              <div className="lb-label">Receitas</div>
              <BadgeCheck className="w-4 h-4 text-emerald-700" />
            </div>
            <div className="mt-2 text-xl lb-money text-emerald-700">{formatCurrency(18420.6)}</div>
            <div className="text-xs text-slate-600 mt-1">+4,2% vs mês anterior</div>
          </div>
          <div className="lb-card lb-card-info lb-card-compact bg-white/95">
            <div className="flex items-center justify-between">
              <div className="lb-label">Despesas</div>
              <ArrowDownUp className="w-4 h-4 text-rose-600" />
            </div>
            <div className="mt-2 text-xl lb-money text-rose-600">{formatCurrency(9720.3)}</div>
            <div className="text-xs text-slate-600 mt-1">-2,1% vs mês anterior</div>
          </div>
          <div className="lb-card lb-card-info lb-card-compact bg-white/95">
            <div className="flex items-center justify-between">
              <div className="lb-label">Limite disponível</div>
              <CreditCard className="w-4 h-4 text-slate-700" />
            </div>
            <div className="mt-2 text-xl lb-money text-slate-900">{formatCurrency(12800)}</div>
            <div className="text-xs text-slate-600 mt-1">Cartão corporate • 4x</div>
          </div>
          <div className="lb-card lb-card-info lb-card-compact bg-white/95">
            <div className="flex items-center justify-between">
              <div className="lb-label">Investimentos</div>
              <PiggyBank className="w-4 h-4 text-slate-700" />
            </div>
            <div className="mt-2 text-xl lb-money text-slate-900">{formatCurrency(84250)}</div>
            <div className="text-xs text-slate-600 mt-1">Rentab. 10,4% a.a.</div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-5">
        <div className="lb-card lb-card-info lb-card-elevated p-5">
          <div className="flex items-center justify-between">
            <div>
              <div className="lb-label">Fluxo de caixa</div>
              <div className="lb-title">Evolução mensal</div>
              <div className="lb-subtitle">Receitas e despesas dos últimos 8 períodos.</div>
            </div>
            <span className="lb-badge lb-badge-success">Estável</span>
          </div>
          <div className="mt-4 lb-chart-grid rounded-sm border border-slate-200 p-4">
            <svg viewBox="0 0 360 120" className="w-full h-28">
              <path
                d="M0 80 L45 68 L90 74 L135 48 L180 62 L225 40 L270 58 L315 36 L360 42"
                fill="none"
                stroke="#0f172a"
                strokeWidth="2"
              />
              <path
                d="M0 92 L45 100 L90 88 L135 98 L180 86 L225 102 L270 96 L315 104 L360 90"
                fill="none"
                stroke="#94a3b8"
                strokeWidth="2"
              />
            </svg>
            <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-slate-600">
              <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-slate-900" />Receitas</div>
              <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-slate-400" />Despesas</div>
              <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-600" />Resultado líquido</div>
              <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-rose-600" />Alertas</div>
            </div>
          </div>
        </div>

        <div className="lb-card lb-card-info lb-card-elevated p-5 space-y-4">
          <div>
            <div className="lb-label">Alocação</div>
            <div className="lb-title">Carteira consolidada</div>
          </div>
          <div className="space-y-3">
            {portfolio.map((item) => (
              <div key={item.label}>
                <div className="flex items-center justify-between text-xs text-slate-600">
                  <span>{item.label}</span>
                  <span className="lb-money text-slate-900">{item.value}%</span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-slate-100">
                  <div className={`h-2 rounded-full ${item.color}`} style={{ width: `${item.value}%` }} />
                </div>
              </div>
            ))}
          </div>
          <div className="lb-divider" />
          <div className="space-y-2 text-xs text-slate-600">
            <div className="flex items-center justify-between">
              <span>Rentabilidade 12m</span>
              <span className="lb-money text-emerald-700">+9,6%</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Risco agregado</span>
              <span className="lb-badge lb-badge-warning">Moderado</span>
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="lb-card lb-card-info lb-card-elevated p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="lb-label">Conta</div>
              <div className="lb-title">Resumo operacional</div>
            </div>
            <Wallet className="w-4 h-4 text-slate-700" />
          </div>
          <div className="mt-3 text-xs text-slate-600 space-y-1">
            <div>Saldo bloqueado: <span className="lb-money text-slate-900">{formatCurrency(2200)}</span></div>
            <div>Saldo projetado: <span className="lb-money text-emerald-700">{formatCurrency(14250)}</span></div>
            <div>Última conciliação: 10:42</div>
          </div>
        </div>
        <div className="lb-card lb-card-info lb-card-elevated p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="lb-label">Cartões</div>
              <div className="lb-title">Faturas e limites</div>
            </div>
            <CreditCard className="w-4 h-4 text-slate-700" />
          </div>
          <div className="mt-3 text-xs text-slate-600 space-y-1">
            <div>Fatura atual: <span className="lb-money text-rose-600">{formatCurrency(3180)}</span></div>
            <div>Vencimento: 12/02</div>
            <div>Limite total: <span className="lb-money text-slate-900">{formatCurrency(24000)}</span></div>
          </div>
        </div>
        <div className="lb-card lb-card-info lb-card-elevated p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="lb-label">Investimentos</div>
              <div className="lb-title">Performance diária</div>
            </div>
            <Landmark className="w-4 h-4 text-slate-700" />
          </div>
          <div className="mt-3 text-xs text-slate-600 space-y-1">
            <div>Ganhos do dia: <span className="lb-money text-emerald-700">{formatCurrency(420.7)}</span></div>
            <div>Aporte programado: 30/01</div>
            <div>Alocação protegida: 62%</div>
          </div>
        </div>
      </section>

      <section className="lb-card lb-card-info lb-card-elevated p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="lb-label">Ações rápidas</div>
            <div className="lb-title">Operações prioritárias</div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => setIsPixOpen(true)} className="lb-action-btn lb-btn-primary">Pix</button>
            <button onClick={() => setIsTransferOpen(true)} className="lb-action-btn lb-btn-secondary">Transferir</button>
            <button onClick={() => navigate('/app/cards')} className="lb-action-btn lb-btn-ghost">Gerenciar cartões</button>
            <button onClick={() => navigate('/app/loans')} className="lb-action-btn lb-btn-ghost">Simular crédito</button>
          </div>
        </div>
      </section>

      <section className="lb-card lb-card-info lb-card-elevated p-5">
        <div className="lb-label">Transações</div>
        <h2 className="lb-title mt-1">Extrato recente</h2>
        <div className="mt-3 border border-slate-300 rounded-sm overflow-hidden">
          <div className="grid grid-cols-5 lb-label lb-table-head font-semibold">
            <div className="px-3 py-2">Data</div>
            <div className="px-3 py-2">Tipo</div>
            <div className="px-3 py-2">Categoria</div>
            <div className="px-3 py-2">Valor</div>
            <div className="px-3 py-2">Status</div>
          </div>
          {loading ? (
            <div className="px-3 py-6 text-xs text-slate-500">Carregando extrato bancário.</div>
          ) : transactions.length === 0 ? (
            <div className="px-4 py-8 text-center">
              <div className="mx-auto mb-3 w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-slate-500" />
              </div>
              <div className="text-sm font-semibold text-slate-800">Nenhuma movimentação registrada</div>
              <div className="text-xs text-slate-500 mt-1">Integrações e conciliações aparecerão aqui assim que forem processadas.</div>
              <button onClick={() => navigate('/app/payments')} className="mt-4 lb-action-btn lb-btn-secondary">
                Iniciar transferência
              </button>
            </div>
          ) : (
            transactions.map((tx, idx) => (
              <div key={idx} className="grid grid-cols-5 text-sm border-t border-slate-300">
                <div className="px-3 py-2 text-xs text-slate-600">
                  {tx.date ? format(new Date(tx.date), 'dd/MM/yyyy HH:mm') : 'Hoje'}
                </div>
                <div className="px-3 py-2 text-xs text-slate-700">
                  {tx.description || (tx.type === 'DEPOSIT' ? 'Depósito Pix' : 'Transferência enviada')}
                </div>
                <div className="px-3 py-2 text-xs text-slate-600">
                  {tx.type === 'DEPOSIT' ? 'Receita' : 'Despesa'}
                </div>
                <div className={`px-3 py-2 text-xs lb-money ${tx.type === 'DEPOSIT' ? 'text-emerald-700' : 'text-rose-600'}`}>
                  {tx.type === 'DEPOSIT' ? '+' : '-'}{formatCurrency(tx.amount)}
                </div>
                <div className="px-3 py-2 text-xs">
                  <span className={`lb-badge ${tx.type === 'DEPOSIT' ? 'lb-badge-success' : 'lb-badge-warning'}`}>
                    Confirmado
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="lb-card lb-card-info lb-card-compact">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="lb-label">Integridade do ledger</div>
            <div className="lb-title">Validação de registros</div>
            <div className="text-xs text-slate-600 mt-1">Confirmação de imutabilidade e consistência dos lançamentos.</div>
          </div>
          <button onClick={checkIntegrity} className="lb-audit-btn">
            {integrityLoading ? 'Verificando' : 'Verificar'}
          </button>
        </div>
        {integrity && (
          <div className="mt-3 text-xs text-slate-600">
            {integrity.ok ? `OK - ${integrity.count} registros validados` : `Falha na transação ${integrity.tx_id}`}
          </div>
        )}
      </section>

      <TransferModal
        isOpen={isTransferOpen}
        onClose={() => setIsTransferOpen(false)}
        currentBalance={balance || 0}
        onSuccess={() => window.location.reload()}
      />

      <PixModal
        isOpen={isPixOpen}
        onClose={() => setIsPixOpen(false)}
        onSuccess={() => window.location.reload()}
      />
    </div>
  );
}

