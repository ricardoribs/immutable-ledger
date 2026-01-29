import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Investments() {
  const [products, setProducts] = useState<any[]>([]);
  const [holdings, setHoldings] = useState<any[]>([]);
  const [autoInvest, setAutoInvest] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function loadData() {
    const [p, h, a] = await Promise.all([
      api.get('/investments/products'),
      api.get('/investments/holdings'),
      api.get('/investments/auto'),
    ]);
    setProducts(p.data || []);
    setHoldings(h.data || []);
    setAutoInvest(a.data || null);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function handleCreateOrder(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      account_id: Number(form.get('account_id')),
      product_id: Number(form.get('product_id')),
      order_type: String(form.get('order_type')),
      amount: Number(form.get('amount')),
    };
    await api.post('/investments/orders', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  async function handleAutoInvest(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      account_id: Number(form.get('account_id')),
      product_id: Number(form.get('product_id')),
      min_balance: Number(form.get('min_balance')),
      enabled: form.get('enabled') === 'on',
    };
    await api.post('/investments/auto', payload);
    await loadData();
    setLoading(false);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Investimentos</h1>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Produtos</h2>
        <div className="space-y-2">
          {products.map((p) => (
            <div key={p.id} className="flex justify-between border-b border-slate-100 pb-2 text-sm">
              <span>{p.name}</span>
              <span>{p.product_type}</span>
              <span>{p.rate}%</span>
              <span>{p.liquidity}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Aplicar/Resgatar</h2>
        <form onSubmit={handleCreateOrder} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="account_id" required placeholder="Conta ID" className="border p-2 rounded" />
          <input name="product_id" required placeholder="Produto ID" className="border p-2 rounded" />
          <select name="order_type" className="border p-2 rounded">
            <option value="BUY">Aplicar</option>
            <option value="SELL">Resgatar</option>
          </select>
          <input name="amount" required placeholder="Quantidade" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Confirmar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Renda automática</h2>
        <form onSubmit={handleAutoInvest} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="account_id" required placeholder="Conta ID" className="border p-2 rounded" defaultValue={autoInvest?.account_id || ''} />
          <input name="product_id" required placeholder="Produto ID" className="border p-2 rounded" defaultValue={autoInvest?.product_id || ''} />
          <input name="min_balance" placeholder="Saldo mínimo" className="border p-2 rounded" defaultValue={autoInvest?.min_balance || 1000} />
          <label className="flex items-center gap-2">
            <input type="checkbox" name="enabled" defaultChecked={autoInvest?.enabled ?? true} />
            Ativar renda automática
          </label>
          <button disabled={loading} className="bg-brand-dark text-white py-2 rounded">Salvar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Carteira</h2>
        <div className="space-y-2">
          {holdings.map((h) => (
            <div key={h.id} className="flex justify-between border-b border-slate-100 pb-2 text-sm">
              <span>Produto {h.product_id}</span>
              <span>{h.quantity}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

