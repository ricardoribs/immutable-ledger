import React, { useState, useEffect } from 'react';
import api from '../services/api';

interface PixKey {
  key: string;
  key_type: string;
  active: boolean;
}

interface AccountResponse {
  balance: number;
  pix_keys: PixKey[];
}

type TabType = 'transfer' | 'keys' | 'charges' | 'limits' | 'schedule' | 'refunds';

type PixCharge = {
  id: number;
  tx_id: string;
  status: string;
  amount?: number | null;
  description?: string | null;
  payload?: string | null;
  qr_code_base64?: string | null;
};

export default function PixArea() {
  const [activeTab, setActiveTab] = useState<TabType>('transfer');
  const [balance, setBalance] = useState(0);
  const [myKeys, setMyKeys] = useState<PixKey[]>([]);
  const [charges, setCharges] = useState<PixCharge[]>([]);
  const [limits, setLimits] = useState<any>(null);
  const [schedules, setSchedules] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedChargeId, setExpandedChargeId] = useState<number | null>(null);
  const [payAmounts, setPayAmounts] = useState<Record<number, string>>({});
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    fetchAll();
  }, []);

  const fetchAll = async () => {
    try {
      const [acc, ch, lim, sch] = await Promise.all([
        api.get<AccountResponse>('/ledger/accounts/me'),
        api.get('/pix/charges'),
        api.get('/pix/limits'),
        api.get('/pix/schedules'),
      ]);
      setBalance(acc.data.balance);
      setMyKeys(acc.data.pix_keys || []);
      setCharges(ch.data || []);
      setLimits(lim.data || null);
      setSchedules(sch.data || []);
    } catch (error) {
      console.error('Erro ao carregar dados', error);
    }
  };

  const handleTransfer = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    const formData = new FormData(e.currentTarget);
    const amountVal = parseFloat(formData.get('amount') as string);
    const pixKey = formData.get('pix_key') as string;

    const data = {
      pix_key: pixKey,
      amount: amountVal,
      idempotency_key: `pix_${Date.now()}`,
    };

    try {
      await api.post('/ledger/pix/transfer', data);
      setMessage({ type: 'success', text: 'Transferência realizada com sucesso!' });
      fetchAll();
      (e.target as HTMLFormElement).reset();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Erro na transferência';
      setMessage({ type: 'error', text: errorMsg });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.currentTarget);
    const data = {
      key: formData.get('key_value') as string,
      key_type: formData.get('key_type') as string,
    };

    try {
      await api.post('/ledger/pix/keys', data);
      setMessage({ type: 'success', text: 'Chave cadastrada com sucesso!' });
      fetchAll();
      (e.target as HTMLFormElement).reset();
    } catch (error: any) {
      setMessage({ type: 'error', text: error.response?.data?.detail || 'Erro ao criar chave' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCharge = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.currentTarget);
    const payload = {
      amount: formData.get('amount') ? Number(formData.get('amount')) : null,
      description: String(formData.get('description') || ''),
      expires_at: formData.get('expires_at') ? String(formData.get('expires_at')) : null,
    };
    await api.post('/pix/charges', payload);
    await fetchAll();
    setLoading(false);
    e.currentTarget.reset();
  };

  const handlePayCharge = async (chargeId: number) => {
    setLoading(true);
    const amount = payAmounts[chargeId];
    const payload = {
      charge_id: chargeId,
      amount: amount ? Number(amount) : null,
    };
    await api.post('/pix/charges/pay', payload);
    await fetchAll();
    setLoading(false);
  };

  const handleUpdateLimits = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.currentTarget);
    const payload = {
      day_limit: Number(formData.get('day_limit')),
      night_limit: Number(formData.get('night_limit')),
      per_tx_limit: Number(formData.get('per_tx_limit')),
      monthly_limit: Number(formData.get('monthly_limit')),
    };
    await api.post('/pix/limits', payload);
    await fetchAll();
    setLoading(false);
  };

  const handleSchedule = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.currentTarget);
    const payload = {
      pix_key: String(formData.get('pix_key')),
      amount: Number(formData.get('amount')),
      scheduled_for: String(formData.get('scheduled_for')),
    };
    await api.post('/pix/schedules', payload);
    await fetchAll();
    setLoading(false);
    e.currentTarget.reset();
  };

  const handleRefund = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    const formData = new FormData(e.currentTarget);
    const payload = {
      charge_id: Number(formData.get('charge_id')),
      amount: Number(formData.get('amount')),
      reason: String(formData.get('reason') || ''),
    };
    await api.post('/pix/refunds', payload);
    await fetchAll();
    setLoading(false);
    e.currentTarget.reset();
  };

  const tabs: { id: TabType; label: string }[] = [
    { id: 'transfer', label: 'Transferir' },
    { id: 'keys', label: 'Minhas chaves' },
    { id: 'charges', label: 'Cobranças' },
    { id: 'limits', label: 'Limites' },
    { id: 'schedule', label: 'Agendamentos' },
    { id: 'refunds', label: 'Devoluções' },
  ];

  return (
    <div className="lb-card lb-card-info p-4 max-w-4xl mx-auto space-y-4">
      <div className="flex justify-between items-center border-b pb-4">
        <h2 className="text-2xl font-bold text-brand-ink">Área Pix</h2>
        <div className="text-right">
          <p className="text-sm text-slate-500">Saldo disponível</p>
          <p className="text-xl font-bold text-brand-primary">
            {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(balance)}
          </p>
        </div>
      </div>

      {message.text && (
        <div className={`p-4 rounded ${message.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'}`}>
          {message.text}
        </div>
      )}

      <div className="flex flex-wrap gap-3 border-b border-slate-100 pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`py-2 px-4 rounded-full text-sm ${activeTab === tab.id ? 'bg-brand-primary text-white' : 'text-slate-500 border border-slate-200'}`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="mt-6">
        {activeTab === 'transfer' && (
          <form onSubmit={handleTransfer} className="space-y-4 max-w-lg">
            <div>
              <label className="block text-sm font-medium text-slate-700">Chave Pix</label>
              <input name="pix_key" required placeholder="CPF, email, telefone..." className="mt-1 block w-full rounded border p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Valor (R$)</label>
              <input name="amount" type="number" step="0.01" required placeholder="0,00" className="mt-1 block w-full rounded border p-2" />
            </div>
            <button type="submit" disabled={loading} className="w-full py-2 bg-brand-primary text-white rounded disabled:opacity-50">
              {loading ? 'Enviando...' : 'Transferir'}
            </button>
          </form>
        )}

        {activeTab === 'keys' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold mb-4">Minhas chaves</h3>
              <ul className="space-y-2">
                {myKeys.map((k) => (
                  <li key={k.key} className="flex justify-between bg-slate-50 p-2 rounded border">
                    <span>{k.key}</span>
                    <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-1 rounded">{k.key_type}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-slate-50 p-4 rounded border">
              <h3 className="font-semibold mb-2">Nova chave</h3>
              <form onSubmit={handleCreateKey} className="space-y-3">
                <select name="key_type" className="w-full p-2 border rounded">
                  <option value="EMAIL">Email</option>
                  <option value="CPF">CPF</option>
                  <option value="PHONE">Telefone</option>
                  <option value="EVP">Aleatória</option>
                </select>
                <input name="key_value" required className="w-full p-2 border rounded" placeholder="Valor da chave" />
                <button type="submit" disabled={loading} className="w-full py-2 bg-brand-primary text-white rounded">Cadastrar</button>
              </form>
            </div>
          </div>
        )}

        {activeTab === 'charges' && (
          <div className="space-y-4">
            <form onSubmit={handleCreateCharge} className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input name="amount" placeholder="Valor (opcional, cobrança estática)" className="border p-2 rounded" />
              <input name="description" placeholder="Descrição" className="border p-2 rounded" />
              <input name="expires_at" placeholder="YYYY-MM-DD" className="border p-2 rounded" />
              <button className="bg-brand-primary text-white py-2 rounded">Gerar cobrança</button>
            </form>
            <div className="space-y-3">
              {charges.map((c) => (
                <div key={c.id} className="border border-slate-100 rounded-xl p-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <div className="font-semibold text-brand-ink">{c.tx_id}</div>
                      <div className="text-xs text-slate-500">{c.status} {c.amount ? `- R$ ${Number(c.amount).toFixed(2)}` : '- Cobrança sem valor'}</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => setExpandedChargeId(expandedChargeId === c.id ? null : c.id)}
                        className="px-3 py-1 text-sm border rounded"
                      >
                        {expandedChargeId === c.id ? 'Ocultar QR' : 'Ver QR'}
                      </button>
                      <button
                        onClick={() => handlePayCharge(c.id)}
                        className="px-3 py-1 text-sm bg-brand-dark text-white rounded"
                      >
                        Pagar
                      </button>
                    </div>
                  </div>
                  {expandedChargeId === c.id && (
                    <div className="mt-3 grid grid-cols-1 md:grid-cols-[160px_1fr] gap-3 items-center">
                      {c.qr_code_base64 && (
                        <img src={`data:image/png;base64,${c.qr_code_base64}`} alt="QR Code Pix" className="w-40 h-40 border rounded" />
                      )}
                      <div className="space-y-2">
                        <input
                          value={payAmounts[c.id] || ''}
                          onChange={(e) => setPayAmounts((prev) => ({ ...prev, [c.id]: e.target.value }))}
                          placeholder="Valor para pagamento (opcional)"
                          className="border p-2 rounded w-full"
                        />
                        {c.payload && (
                          <textarea readOnly value={c.payload} className="border p-2 rounded w-full h-24 text-xs" />
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'limits' && limits && (
          <form onSubmit={handleUpdateLimits} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input name="day_limit" defaultValue={limits.day_limit} placeholder="Limite diurno" className="border p-2 rounded" />
            <input name="night_limit" defaultValue={limits.night_limit} placeholder="Limite noturno" className="border p-2 rounded" />
            <input name="per_tx_limit" defaultValue={limits.per_tx_limit} placeholder="Limite por transação" className="border p-2 rounded" />
            <input name="monthly_limit" defaultValue={limits.monthly_limit} placeholder="Limite mensal" className="border p-2 rounded" />
            <button className="bg-brand-primary text-white py-2 rounded">Salvar</button>
          </form>
        )}

        {activeTab === 'schedule' && (
          <div className="space-y-4">
            <form onSubmit={handleSchedule} className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input name="pix_key" required placeholder="Chave" className="border p-2 rounded" />
              <input name="amount" required placeholder="Valor" className="border p-2 rounded" />
              <input name="scheduled_for" required placeholder="YYYY-MM-DD" className="border p-2 rounded" />
              <button className="bg-brand-primary text-white py-2 rounded">Agendar</button>
            </form>
            <div className="space-y-2">
              {schedules.map((s) => (
                <div key={s.id} className="flex justify-between border-b border-slate-100 pb-2">
                  <span>{s.pix_key}</span>
                  <span>{s.status}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'refunds' && (
          <form onSubmit={handleRefund} className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <input name="charge_id" required placeholder="ID da cobrança" className="border p-2 rounded" />
            <input name="amount" required placeholder="Valor" className="border p-2 rounded" />
            <input name="reason" placeholder="Motivo" className="border p-2 rounded" />
            <button className="bg-brand-primary text-white py-2 rounded">Solicitar estorno</button>
          </form>
        )}
      </div>
    </div>
  );
}
