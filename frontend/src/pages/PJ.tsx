import { useEffect, useState } from 'react';
import api from '../services/api';

export default function PJ() {
  const [businesses, setBusinesses] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function loadData() {
    const res = await api.get('/pj/businesses');
    setBusinesses(res.data || []);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function handleCreateBusiness(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      name: String(form.get('name')),
      cnpj: String(form.get('cnpj')),
    };
    await api.post('/pj/businesses', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Pessoa JurÃ­dica</h1>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Cadastrar Empresa</h2>
        <form onSubmit={handleCreateBusiness} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="name" required placeholder="Nome" className="border p-2 rounded" />
          <input name="cnpj" required placeholder="CNPJ" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Salvar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Empresas</h2>
        <div className="space-y-2">
          {businesses.map((b) => (
            <div key={b.id} className="flex justify-between border-b border-slate-100 pb-2">
              <span>{b.name}</span>
              <span>{b.cnpj}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}


