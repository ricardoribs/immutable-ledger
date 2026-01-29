import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Billing() {
  const [boletos, setBoletos] = useState<any[]>([]);
  const [links, setLinks] = useState<any[]>([]);
  const [posSales, setPosSales] = useState<any[]>([]);
  const [splits, setSplits] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function loadData() {
    const [b, l, p, s] = await Promise.all([
      api.get('/billing/boletos'),
      api.get('/billing/links'),
      api.get('/billing/pos'),
      api.get('/billing/split'),
    ]);
    setBoletos(b.data || []);
    setLinks(l.data || []);
    setPosSales(p.data || []);
    setSplits(s.data || []);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function handleCreateBoleto(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      amount: Number(form.get('amount')),
      description: String(form.get('description') || ''),
      due_date: String(form.get('due_date')),
    };
    await api.post('/billing/boletos', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  async function handlePayBoleto(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      boleto_id: Number(form.get('boleto_id')),
    };
    await api.post('/billing/boletos/pay', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  async function handleCreateLink(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = { amount: Number(form.get('amount')) };
    await api.post('/billing/links', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  async function handleCreatePosSale(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = { amount: Number(form.get('amount')) };
    await api.post('/billing/pos', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  async function handleCreateSplit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      name: String(form.get('name')),
      percentage: Number(form.get('percentage')),
    };
    await api.post('/billing/split', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Cobrança e recebíveis</h1>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Gerar boleto</h2>
        <form onSubmit={handleCreateBoleto} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="amount" required placeholder="Valor" className="border p-2 rounded" />
          <input name="description" placeholder="Descrição" className="border p-2 rounded" />
          <input name="due_date" required placeholder="YYYY-MM-DD" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Gerar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Pagar boleto</h2>
        <form onSubmit={handlePayBoleto} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="boleto_id" required placeholder="ID do boleto" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-dark text-white py-2 rounded">Pagar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Links de pagamento</h2>
        <form onSubmit={handleCreateLink} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="amount" required placeholder="Valor" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Criar link</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Vendas no POS</h2>
        <form onSubmit={handleCreatePosSale} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="amount" required placeholder="Valor" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Registrar venda</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Split de recebíveis</h2>
        <form onSubmit={handleCreateSplit} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="name" required placeholder="Nome da regra" className="border p-2 rounded" />
          <input name="percentage" required placeholder="Percentual" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-dark text-white py-2 rounded">Criar split</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Boletos</h2>
        <div className="space-y-2">
          {boletos.map((b) => (
            <div key={b.id} className="flex flex-wrap justify-between border-b border-slate-100 pb-2 text-sm">
              <span>{b.barcode}</span>
              <span>R$ {Number(b.amount).toFixed(2)}</span>
              <span>{b.status}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Links</h2>
        <div className="space-y-2">
          {links.map((l) => (
            <div key={l.id} className="flex flex-wrap justify-between border-b border-slate-100 pb-2 text-sm">
              <span>{l.url}</span>
              <span>R$ {Number(l.amount).toFixed(2)}</span>
              <span>{l.status}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">POS</h2>
        <div className="space-y-2">
          {posSales.map((p) => (
            <div key={p.id} className="flex flex-wrap justify-between border-b border-slate-100 pb-2 text-sm">
              <span>Venda #{p.id}</span>
              <span>R$ {Number(p.amount).toFixed(2)}</span>
              <span>{p.status}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Split</h2>
        <div className="space-y-2">
          {splits.map((s) => (
            <div key={s.id} className="flex justify-between border-b border-slate-100 pb-2 text-sm">
              <span>{s.name}</span>
              <span>{s.percentage}%</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

