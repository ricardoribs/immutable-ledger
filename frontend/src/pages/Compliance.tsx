import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Compliance() {
  const [consents, setConsents] = useState<any[]>([]);
  const [forgetRequests, setForgetRequests] = useState<any[]>([]);
  const [report, setReport] = useState<any>(null);

  async function loadData() {
    const [c, r] = await Promise.all([
      api.get('/compliance/consents'),
      api.get('/compliance/report'),
    ]);
    setConsents(c.data || []);
    setReport(r.data || null);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function handleConsent(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = {
      consent_type: String(form.get('consent_type')),
      details: String(form.get('details') || ''),
    };
    await api.post('/compliance/consents', payload);
    await loadData();
    e.currentTarget.reset();
  }

  async function requestForget() {
    const res = await api.post('/compliance/forget', {});
    setForgetRequests((prev) => [...prev, res.data]);
  }

  async function completeForget(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const id = Number(form.get('request_id'));
    await api.post(`/compliance/forget/${id}/complete`, {});
    await loadData();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">LGPD e privacidade</h1>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Consentimentos</h2>
        <form onSubmit={handleConsent} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <select name="consent_type" className="border p-2 rounded">
            <option value="PRIVACY">Privacidade</option>
            <option value="MARKETING">Marketing</option>
            <option value="DATA_SHARING">Compartilhamento de dados</option>
          </select>
          <input name="details" placeholder="Detalhes (opcional)" className="border p-2 rounded" />
          <button className="bg-brand-primary text-white py-2 rounded">Registrar consentimento</button>
        </form>
        <div className="mt-4 space-y-2">
          {consents.map((c) => (
            <div key={c.id} className="flex justify-between border-b border-slate-100 pb-2 text-sm">
              <span>{c.consent_type}</span>
              <span className="text-slate-500">{c.given_at}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Direito ao esquecimento</h2>
        <div className="flex flex-wrap gap-3">
          <button onClick={requestForget} className="bg-brand-dark text-white px-4 py-2 rounded">
            Solicitar anonimização
          </button>
          <form onSubmit={completeForget} className="flex gap-2">
            <input name="request_id" placeholder="ID da solicitação" className="border p-2 rounded" />
            <button className="border border-slate-200 px-4 py-2 rounded">Concluir</button>
          </form>
        </div>
        {forgetRequests.length > 0 && (
          <div className="mt-3 space-y-2 text-sm">
            {forgetRequests.map((r) => (
              <div key={r.id} className="flex justify-between border-b border-slate-100 pb-2">
                <span>Solicitação #{r.id}</span>
                <span>{r.status}</span>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Relatório de dados pessoais</h2>
        {report ? (
          <div className="text-sm text-slate-700 space-y-1">
            <div>Nome: {report.name}</div>
            <div>Email: {report.email}</div>
            <div>CPF (final): {report.cpf_last4}</div>
          </div>
        ) : (
          <div className="text-sm text-slate-500">Carregando relatório...</div>
        )}
      </section>
    </div>
  );
}

