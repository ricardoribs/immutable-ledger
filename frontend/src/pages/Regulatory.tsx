import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Regulatory() {
  const [alerts, setAlerts] = useState<any[]>([]);
  const [scr, setScr] = useState<any>(null);
  const [coaf, setCoaf] = useState<any>(null);

  async function loadAlerts() {
    const res = await api.get('/regulatory/aml/alerts');
    setAlerts(res.data || []);
  }

  useEffect(() => {
    loadAlerts().catch(() => {});
  }, []);

  async function handleKyc(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = { document_id: String(form.get('document_id')) };
    await api.post('/regulatory/kyc', payload);
  }

  async function generateScr(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const period = String(form.get('period'));
    const res = await api.get(`/regulatory/scr?period=${period}`);
    setScr(res.data);
  }

  async function generateCoaf(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const period = String(form.get('period'));
    const res = await api.get(`/regulatory/coaf?period=${period}`);
    setCoaf(res.data);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Regulatório & PLD-FT</h1>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">KYC</h2>
        <form onSubmit={handleKyc} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="document_id" required placeholder="Documento (RG/CPF)" className="border p-2 rounded" />
          <button className="bg-brand-primary text-white py-2 rounded">Enviar KYC</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Alertas AML</h2>
        <div className="space-y-2">
          {alerts.map((a) => (
            <div key={a.id} className="flex justify-between border-b border-slate-100 pb-2 text-sm">
              <span>{a.rule}</span>
              <span className="text-slate-500">{a.created_at}</span>
            </div>
          ))}
          {alerts.length === 0 && <div className="text-sm text-slate-500">Nenhum alerta.</div>}
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="lb-card lb-card-info p-4">
          <h2 className="font-semibold mb-3">Relatório SCR</h2>
          <form onSubmit={generateScr} className="flex gap-2">
            <input name="period" placeholder="2026-01" className="border p-2 rounded w-full" />
            <button className="bg-brand-dark text-white px-4 rounded">Gerar</button>
          </form>
          {scr && <pre className="text-xs text-slate-600 mt-3 whitespace-pre-wrap">{scr.content}</pre>}
        </div>
        <div className="lb-card lb-card-info p-4">
          <h2 className="font-semibold mb-3">Relatório COAF</h2>
          <form onSubmit={generateCoaf} className="flex gap-2">
            <input name="period" placeholder="2026-01" className="border p-2 rounded w-full" />
            <button className="bg-brand-dark text-white px-4 rounded">Gerar</button>
          </form>
          {coaf && <pre className="text-xs text-slate-600 mt-3 whitespace-pre-wrap">{coaf.content}</pre>}
        </div>
      </section>
    </div>
  );
}

