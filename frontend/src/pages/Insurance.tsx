import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Insurance() {
  const [policies, setPolicies] = useState<any[]>([]);
  const [claims, setClaims] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function loadData() {
    const [p, c] = await Promise.all([
      api.get('/insurance/policies'),
      api.get('/insurance/claims'),
    ]);
    setPolicies(p.data || []);
    setClaims(c.data || []);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function handleCreatePolicy(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      policy_type: String(form.get('policy_type')),
      premium: Number(form.get('premium')),
      details: String(form.get('details') || ''),
    };
    await api.post('/insurance/policies', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  async function handleCreateClaim(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      policy_id: Number(form.get('policy_id')),
      description: String(form.get('description') || ''),
    };
    await api.post('/insurance/claims', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Seguros</h1>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Contratar Seguro</h2>
        <form onSubmit={handleCreatePolicy} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <select name="policy_type" className="border p-2 rounded">
            <option value="LIFE">Vida</option>
            <option value="HOME">Residencial</option>
            <option value="AUTO">Auto</option>
            <option value="TRAVEL">Viagem</option>
          </select>
          <input name="premium" required placeholder="Prêmio mensal" className="border p-2 rounded" />
          <input name="details" placeholder="Detalhes" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Contratar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Apólices</h2>
        <div className="space-y-2">
          {policies.map((p) => (
            <div key={p.id} className="flex justify-between border-b border-slate-100 pb-2">
              <span>{p.policy_type}</span>
              <span>{p.status}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Acionar Seguro</h2>
        <form onSubmit={handleCreateClaim} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="policy_id" required placeholder="Apólice ID" className="border p-2 rounded" />
          <input name="description" placeholder="Descrição" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Abrir Sinistro</button>
        </form>
        <div className="mt-4 space-y-2">
          {claims.map((c) => (
            <div key={c.id} className="flex justify-between border-b border-slate-100 pb-2">
              <span>Sinistro {c.id}</span>
              <span>{c.status}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}



