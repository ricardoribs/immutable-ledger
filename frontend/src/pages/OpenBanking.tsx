import { useEffect, useState } from 'react';
import api from '../services/api';

export default function OpenBanking() {
  const [consents, setConsents] = useState<any[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function loadData() {
    const [c, a] = await Promise.all([
      api.get('/open-banking/consents'),
      api.get('/open-banking/external-accounts'),
    ]);
    setConsents(c.data || []);
    setAccounts(a.data || []);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function handleCreateConsent(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      institution: String(form.get('institution')),
      scope: String(form.get('scope') || ''),
    };
    await api.post('/open-banking/consents', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  async function handleAddAccount(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      institution: String(form.get('institution')),
      account_ref: String(form.get('account_ref')),
      balance: Number(form.get('balance')),
    };
    await api.post('/open-banking/external-accounts', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Open Finance</h1>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Consentimentos</h2>
        <form onSubmit={handleCreateConsent} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="institution" required placeholder="Instituição" className="border p-2 rounded" />
          <input name="scope" placeholder="Escopo" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Autorizar</button>
        </form>
        <div className="mt-4 space-y-2">
          {consents.map((c) => (
            <div key={c.id} className="flex justify-between border-b border-slate-100 pb-2">
              <span>{c.institution}</span>
              <span>{c.status}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Contas Externas</h2>
        <form onSubmit={handleAddAccount} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="institution" required placeholder="Instituição" className="border p-2 rounded" />
          <input name="account_ref" required placeholder="Referência" className="border p-2 rounded" />
          <input name="balance" placeholder="Saldo" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Adicionar</button>
        </form>
        <div className="mt-4 space-y-2">
          {accounts.map((a) => (
            <div key={a.id} className="flex justify-between border-b border-slate-100 pb-2">
              <span>{a.institution}</span>
              <span>{a.balance}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}



