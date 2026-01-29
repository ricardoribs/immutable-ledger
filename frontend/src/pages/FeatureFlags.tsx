import { useEffect, useState } from 'react';
import api from '../services/api';

export default function FeatureFlags() {
  const [flags, setFlags] = useState<any[]>([]);

  async function loadData() {
    const res = await api.get('/feature-flags');
    setFlags(res.data || []);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function handleSet(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = {
      name: String(form.get('name')),
      enabled: form.get('enabled') === 'on',
    };
    await api.post('/feature-flags', payload);
    await loadData();
    e.currentTarget.reset();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Flags de funcionalidades</h1>
      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Nova flag</h2>
        <form onSubmit={handleSet} className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input name="name" placeholder="nome_da_funcionalidade" className="border p-2 rounded" />
          <label className="flex items-center gap-2 border p-2 rounded">
            <input type="checkbox" name="enabled" /> Ativa
          </label>
          <button className="bg-brand-primary text-white py-2 rounded">Salvar</button>
        </form>
      </section>
      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Flags atuais</h2>
        <div className="space-y-2">
          {flags.map((f) => (
            <div key={f.id} className="flex justify-between border-b border-slate-100 pb-2 text-sm">
              <span>{f.name}</span>
              <span className={f.enabled ? 'text-emerald-600' : 'text-slate-500'}>
                {f.enabled ? 'Ativa' : 'Desativada'}
              </span>
            </div>
          ))}
          {flags.length === 0 && <div className="text-sm text-slate-500">Nenhuma flag cadastrada.</div>}
        </div>
      </section>
    </div>
  );
}


