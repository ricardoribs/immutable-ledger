import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Utilities() {
  const [utilities, setUtilities] = useState<any[]>([]);
  const [donations, setDonations] = useState<any[]>([]);
  const [fxOrders, setFxOrders] = useState<any[]>([]);

  async function loadData() {
    const [u, d, f] = await Promise.all([
      api.get('/utilities'),
      api.get('/utilities/donations'),
      api.get('/utilities/fx'),
    ]);
    setUtilities(u.data || []);
    setDonations(d.data || []);
    setFxOrders(f.data || []);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function handleUtility(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = {
      utility_type: String(form.get('utility_type')),
      provider: String(form.get('provider') || ''),
      amount: Number(form.get('amount')),
    };
    await api.post('/utilities', payload);
    await loadData();
    e.currentTarget.reset();
  }

  async function handleDonation(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = {
      organization: String(form.get('organization')),
      amount: Number(form.get('amount')),
    };
    await api.post('/utilities/donations', payload);
    await loadData();
    e.currentTarget.reset();
  }

  async function handleFx(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = {
      currency: String(form.get('currency')),
      amount: Number(form.get('amount')),
      rate: Number(form.get('rate')),
    };
    await api.post('/utilities/fx', payload);
    await loadData();
    e.currentTarget.reset();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Serviços e utilidades</h1>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Recargas e contas</h2>
        <form onSubmit={handleUtility} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <select name="utility_type" className="border p-2 rounded">
            <option value="RECHARGE">Recarga</option>
            <option value="TV">TV</option>
            <option value="INTERNET">Internet</option>
            <option value="BILLS">Contas</option>
          </select>
          <input name="provider" placeholder="Fornecedor" className="border p-2 rounded" />
          <input name="amount" required placeholder="Valor" className="border p-2 rounded" />
          <button className="bg-brand-primary text-white py-2 rounded">Pagar</button>
        </form>
        <div className="mt-4 space-y-2">
          {utilities.map((u) => (
            <div key={u.id} className="flex justify-between border-b border-slate-100 pb-2">
              <span>{u.utility_type}</span>
              <span>{u.amount}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Doações</h2>
        <form onSubmit={handleDonation} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="organization" required placeholder="ONG" className="border p-2 rounded" />
          <input name="amount" required placeholder="Valor" className="border p-2 rounded" />
          <button className="bg-brand-primary text-white py-2 rounded">Doar</button>
        </form>
        <div className="mt-4 space-y-2">
          {donations.map((d) => (
            <div key={d.id} className="flex justify-between border-b border-slate-100 pb-2">
              <span>{d.organization}</span>
              <span>{d.amount}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Câmbio</h2>
        <form onSubmit={handleFx} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="currency" required placeholder="USD" className="border p-2 rounded" />
          <input name="amount" required placeholder="Valor" className="border p-2 rounded" />
          <input name="rate" required placeholder="Cotação" className="border p-2 rounded" />
          <button className="bg-brand-primary text-white py-2 rounded">Comprar</button>
        </form>
        <div className="mt-4 space-y-2">
          {fxOrders.map((f) => (
            <div key={f.id} className="flex justify-between border-b border-slate-100 pb-2">
              <span>{f.currency}</span>
              <span>{f.amount}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}



