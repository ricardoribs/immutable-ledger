import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Notifications() {
  const [items, setItems] = useState<any[]>([]);

  async function loadData() {
    const res = await api.get('/notifications');
    setItems(res.data || []);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function handleSend(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = {
      channel: String(form.get('channel')),
      subject: String(form.get('subject') || ''),
      message: String(form.get('message')),
    };
    await api.post('/notifications', payload);
    await loadData();
    e.currentTarget.reset();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Notificações</h1>
      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Enviar notificação</h2>
        <form onSubmit={handleSend} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <select name="channel" className="border p-2 rounded">
            <option value="EMAIL">Email</option>
            <option value="SMS">SMS</option>
            <option value="PUSH">Push</option>
            <option value="WHATSAPP">WhatsApp</option>
          </select>
          <input name="subject" placeholder="Assunto" className="border p-2 rounded" />
          <textarea name="message" placeholder="Mensagem" className="border p-2 rounded md:col-span-2" />
          <button className="bg-brand-primary text-white py-2 rounded">Enviar</button>
        </form>
      </section>
      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Histórico</h2>
        <div className="space-y-2">
          {items.map((n) => (
            <div key={n.id} className="flex justify-between border-b border-slate-100 pb-2 text-sm">
              <span>{n.channel} • {n.subject || 'Sem assunto'}</span>
              <span className="text-slate-500">{n.status}</span>
            </div>
          ))}
          {items.length === 0 && <div className="text-sm text-slate-500">Sem notificações.</div>}
        </div>
      </section>
    </div>
  );
}

