import { useState } from 'react';
import api from '../services/api';

export default function Analytics() {
  const [churn, setChurn] = useState<any>(null);
  const [recs, setRecs] = useState<any[]>([]);

  async function predictChurn() {
    const res = await api.post('/ml/churn', {});
    setChurn(res.data);
  }

  async function loadRecommendations() {
    const res = await api.post('/ml/recommendations', {});
    setRecs(res.data || []);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Análises e ML</h1>

      <section className="lb-card lb-card-info p-4 space-y-3">
        <h2 className="font-semibold">Modelos de ML</h2>
        <div className="flex gap-2 flex-wrap">
          <button onClick={predictChurn} className="bg-brand-primary text-white px-4 py-2 rounded">Prever churn</button>
          <button onClick={loadRecommendations} className="border border-slate-200 px-4 py-2 rounded">Gerar recomendações</button>
        </div>
        {churn && <div className="text-sm text-slate-700">Score de churn: {Number(churn.score).toFixed(2)}</div>}
        {recs.length > 0 && (
          <ul className="text-sm text-slate-700 list-disc ml-5">
            {recs.map((r) => <li key={r.id}>{r.content}</li>)}
          </ul>
        )}
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">BI e Armazém de dados</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <a className="border rounded-xl px-4 py-3 hover:bg-brand-light" href="http://localhost:3001" target="_blank" rel="noreferrer">Metabase</a>
          <a className="border rounded-xl px-4 py-3 hover:bg-brand-light" href="http://localhost:8080" target="_blank" rel="noreferrer">Airflow</a>
          <a className="border rounded-xl px-4 py-3 hover:bg-brand-light" href="http://localhost:5433" target="_blank" rel="noreferrer">Armazém de dados</a>
        </div>
      </section>
    </div>
  );
}


