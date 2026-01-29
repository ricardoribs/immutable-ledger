import { useEffect, useState } from 'react';
import api from '../services/api';

interface Beneficiary {
  id: number;
  name: string;
  bank_code?: string;
  agency?: string;
  account?: string;
  cpf_cnpj?: string;
  pix_key?: string;
  favorite: boolean;
}

interface Payment {
  id: number;
  payment_type: string;
  amount: number;
  status: string;
  created_at: string;
  fee_amount?: number;
  spb_protocol?: string | null;
  scheduled_for?: string | null;
}

interface RecurringPayment {
  id: number;
  payment_type: string;
  amount: number;
  interval_days: number;
  active: boolean;
}

export default function Payments() {
  const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [recurring, setRecurring] = useState<RecurringPayment[]>([]);
  const [loading, setLoading] = useState(false);

  async function loadData() {
    const [b, p, r] = await Promise.all([
      api.get('/payments/beneficiaries'),
      api.get('/payments'),
      api.get('/payments/recurring'),
    ]);
    setBeneficiaries(b.data || []);
    setPayments(p.data || []);
    setRecurring(r.data || []);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function handleAddBeneficiary(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      name: String(form.get('name')),
      bank_code: String(form.get('bank_code') || ''),
      agency: String(form.get('agency') || ''),
      account: String(form.get('account') || ''),
      cpf_cnpj: String(form.get('cpf_cnpj') || ''),
      pix_key: String(form.get('pix_key') || ''),
      favorite: Boolean(form.get('favorite')),
    };
    await api.post('/payments/beneficiaries', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  async function handleCreatePayment(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      account_id: Number(form.get('account_id')),
      payment_type: String(form.get('payment_type')),
      amount: Number(form.get('amount')),
      description: String(form.get('description') || ''),
      beneficiary_id: form.get('beneficiary_id') ? Number(form.get('beneficiary_id')) : null,
      scheduled_for: form.get('scheduled_for') ? String(form.get('scheduled_for')) : null,
      to_account_id: form.get('to_account_id') ? Number(form.get('to_account_id')) : null,
    };
    await api.post('/payments', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  async function handleCreateRecurring(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      account_id: Number(form.get('account_id')),
      beneficiary_id: form.get('beneficiary_id') ? Number(form.get('beneficiary_id')) : null,
      payment_type: String(form.get('payment_type')),
      amount: Number(form.get('amount')),
      interval_days: Number(form.get('interval_days')),
    };
    await api.post('/payments/recurring', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Pagamentos</h1>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Cadastrar beneficiÃ¡rio</h2>
        <form onSubmit={handleAddBeneficiary} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="name" required placeholder="Nome" className="border p-2 rounded" />
          <input name="cpf_cnpj" placeholder="CPF/CNPJ" className="border p-2 rounded" />
          <input name="bank_code" placeholder="Banco" className="border p-2 rounded" />
          <input name="agency" placeholder="AgÃªncia" className="border p-2 rounded" />
          <input name="account" placeholder="Conta" className="border p-2 rounded" />
          <input name="pix_key" placeholder="Chave Pix" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Salvar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Novo pagamento</h2>
        <form onSubmit={handleCreatePayment} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="account_id" required placeholder="Conta ID" className="border p-2 rounded" />
          <select name="payment_type" className="border p-2 rounded">
            <option value="TED">TED</option>
            <option value="DOC">DOC</option>
            <option value="BOLETO">Boleto</option>
            <option value="UTILITY">Conta de consumo</option>
            <option value="TAX">Imposto</option>
            <option value="RECHARGE">Recarga</option>
          </select>
          <input name="amount" required placeholder="Valor" className="border p-2 rounded" />
          <input name="description" placeholder="DescriÃ§Ã£o" className="border p-2 rounded" />
          <input name="scheduled_for" placeholder="Agendar (YYYY-MM-DD)" className="border p-2 rounded" />
          <input name="to_account_id" placeholder="Conta destino (interna)" className="border p-2 rounded" />
          <select name="beneficiary_id" className="border p-2 rounded">
            <option value="">BeneficiÃ¡rio (opcional)</option>
            {beneficiaries.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Pagar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">RecorrÃªncias</h2>
        <form onSubmit={handleCreateRecurring} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="account_id" required placeholder="Conta ID" className="border p-2 rounded" />
          <select name="payment_type" className="border p-2 rounded">
            <option value="TED">TED</option>
            <option value="DOC">DOC</option>
            <option value="BOLETO">Boleto</option>
            <option value="UTILITY">Conta de consumo</option>
            <option value="TAX">Imposto</option>
            <option value="RECHARGE">Recarga</option>
          </select>
          <input name="amount" required placeholder="Valor" className="border p-2 rounded" />
          <input name="interval_days" required placeholder="Intervalo (dias)" className="border p-2 rounded" />
          <select name="beneficiary_id" className="border p-2 rounded">
            <option value="">BeneficiÃ¡rio (opcional)</option>
            {beneficiaries.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
          <button disabled={loading} className="bg-brand-dark text-white py-2 rounded">Criar recorrÃªncia</button>
        </form>
        <div className="mt-4 space-y-2">
          {recurring.map((r) => (
            <div key={r.id} className="flex justify-between border-b border-slate-100 pb-2 text-sm">
              <span>{r.payment_type}</span>
              <span>R$ {r.amount.toFixed(2)} ? {r.interval_days} dias</span>
              <span className={r.active ? 'text-emerald-600' : 'text-slate-500'}>{r.active ? 'Ativo' : 'Pausado'}</span>
            </div>
          ))}
          {recurring.length === 0 && <div className="text-sm text-slate-500">Nenhuma recorrÃªncia cadastrada.</div>}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Pagamentos recentes</h2>
        <div className="space-y-2">
          {payments.map((p) => (
            <div key={p.id} className="flex flex-wrap justify-between border-b border-slate-100 pb-2 text-sm">
              <span>{p.payment_type}</span>
              <span>R$ {p.amount.toFixed(2)}</span>
              <span>{p.status}</span>
              <span className="text-slate-500">Taxa: R$ {(p.fee_amount || 0).toFixed(2)}</span>
              <span className="text-slate-500">{p.spb_protocol ? `SPB ${p.spb_protocol}` : 'Sem protocolo'}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

