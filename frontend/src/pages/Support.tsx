import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Support() {
  const [tickets, setTickets] = useState<any[]>([]);
  const [faq, setFaq] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function loadData() {
    const [t, f] = await Promise.all([
      api.get('/support/tickets'),
      api.get('/support/faq'),
    ]);
    setTickets(t.data || []);
    setFaq(f.data || []);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function handleCreateTicket(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      subject: String(form.get('subject')),
      message: String(form.get('message')),
    };
    await api.post('/support/tickets', payload);
    await loadData();
    setLoading(false);
    e.currentTarget.reset();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Atendimento</h1>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Abrir Ticket</h2>
        <form onSubmit={handleCreateTicket} className="grid grid-cols-1 gap-3">
          <input name="subject" required placeholder="Assunto" className="border p-2 rounded" />
          <textarea name="message" required placeholder="Mensagem" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Enviar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Tickets</h2>
        <div className="space-y-2">
          {tickets.map((t) => (
            <div key={t.id} className="flex justify-between border-b border-slate-100 pb-2">
              <span>{t.subject}</span>
              <span>{t.status}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">FAQ</h2>
        <div className="space-y-3">
          {faq.map((f) => (
            <div key={f.id}>
              <div className="font-semibold">{f.question}</div>
              <div className="text-sm text-gray-600">{f.answer}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}


