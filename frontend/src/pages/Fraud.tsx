import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Fraud() {
  const [scores, setScores] = useState<any[]>([]);

  async function loadData() {
    const res = await api.get('/fraud/scores');
    setScores(res.data || []);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Monitoramento de Fraude</h1>

      <section className="lb-card lb-card-info p-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Scores recentes</h2>
          <button onClick={loadData} className="text-sm text-brand-primary">Atualizar</button>
        </div>
        <div className="mt-4 space-y-2">
          {scores.map((s) => (
            <div key={s.id} className="flex justify-between border-b border-slate-100 pb-2 text-sm">
              <div>
                <div className="font-semibold text-brand-ink">Score {Number(s.score).toFixed(2)}</div>
                <div className="text-slate-500">{s.rules}</div>
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-500">{s.created_at}</div>
                <div className="text-xs uppercase text-brand-primary">{s.action}</div>
              </div>
            </div>
          ))}
          {scores.length === 0 && <div className="text-sm text-slate-500">Nenhum evento recente.</div>}
        </div>
      </section>
    </div>
  );
}

