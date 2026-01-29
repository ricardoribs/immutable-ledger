import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Settings() {
  const [profile, setProfile] = useState<any>(null);
  const [notifications, setNotifications] = useState<any>(null);
  const [limits, setLimits] = useState<any>(null);
  const [accessibility, setAccessibility] = useState<any>(null);
  const [privacy, setPrivacy] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function loadData() {
    const [p, n, l, a, pr] = await Promise.all([
      api.get('/settings/profile'),
      api.get('/settings/notifications'),
      api.get('/settings/limits'),
      api.get('/settings/accessibility'),
      api.get('/settings/privacy'),
    ]);
    setProfile(p.data);
    setNotifications(n.data);
    setLimits(l.data);
    setAccessibility(a.data);
    setPrivacy(pr.data);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function handleProfile(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      phone: String(form.get('phone') || ''),
      address: String(form.get('address') || ''),
    };
    const res = await api.post('/settings/profile', payload);
    setProfile(res.data);
    setLoading(false);
  }

  async function handleNotifications(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      email_enabled: form.get('email_enabled') === 'on',
      sms_enabled: form.get('sms_enabled') === 'on',
      push_enabled: form.get('push_enabled') === 'on',
      whatsapp_enabled: form.get('whatsapp_enabled') === 'on',
      quiet_hours: String(form.get('quiet_hours') || ''),
    };
    const res = await api.post('/settings/notifications', payload);
    setNotifications(res.data);
    setLoading(false);
  }

  async function handleLimits(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      pix_limit: Number(form.get('pix_limit')),
      ted_limit: Number(form.get('ted_limit')),
      doc_limit: Number(form.get('doc_limit')),
      withdrawal_limit: Number(form.get('withdrawal_limit')),
    };
    const res = await api.post('/settings/limits', payload);
    setLimits(res.data);
    setLoading(false);
  }

  async function handleAccessibility(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      dark_mode: form.get('dark_mode') === 'on',
      font_scale: Number(form.get('font_scale')),
      high_contrast: form.get('high_contrast') === 'on',
    };
    const res = await api.post('/settings/accessibility', payload);
    setAccessibility(res.data);
    setLoading(false);
  }

  async function handlePrivacy(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      share_data: form.get('share_data') === 'on',
      marketing_emails: form.get('marketing_emails') === 'on',
    };
    const res = await api.post('/settings/privacy', payload);
    setPrivacy(res.data);
    setLoading(false);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">ConfiguraÃ§Ãµes</h1>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Perfil</h2>
        <form onSubmit={handleProfile} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="phone" defaultValue={profile?.phone || ''} placeholder="Telefone" className="border p-2 rounded" />
          <input name="address" defaultValue={profile?.address || ''} placeholder="Endere?o" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Salvar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">NotificaÃ§Ãµes</h2>
        <form onSubmit={handleNotifications} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <label className="flex items-center gap-2">
            <input type="checkbox" name="email_enabled" defaultChecked={notifications?.email_enabled} /> Email
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" name="sms_enabled" defaultChecked={notifications?.sms_enabled} /> SMS
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" name="push_enabled" defaultChecked={notifications?.push_enabled} /> Push
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" name="whatsapp_enabled" defaultChecked={notifications?.whatsapp_enabled} /> WhatsApp
          </label>
          <input name="quiet_hours" defaultValue={notifications?.quiet_hours || ''} placeholder="Hor?rio" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Salvar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Limites</h2>
        <form onSubmit={handleLimits} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="pix_limit" defaultValue={limits?.pix_limit || 0} placeholder="Limite PIX" className="border p-2 rounded" />
          <input name="ted_limit" defaultValue={limits?.ted_limit || 0} placeholder="Limite TED" className="border p-2 rounded" />
          <input name="doc_limit" defaultValue={limits?.doc_limit || 0} placeholder="Limite DOC" className="border p-2 rounded" />
          <input name="withdrawal_limit" defaultValue={limits?.withdrawal_limit || 0} placeholder="Limite saque" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Salvar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Acessibilidade</h2>
        <form onSubmit={handleAccessibility} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <label className="flex items-center gap-2">
            <input type="checkbox" name="dark_mode" defaultChecked={accessibility?.dark_mode} /> Modo escuro
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" name="high_contrast" defaultChecked={accessibility?.high_contrast} /> Alto contraste
          </label>
          <input name="font_scale" defaultValue={accessibility?.font_scale || 1} placeholder="Escala de fonte" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Salvar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Privacidade</h2>
        <form onSubmit={handlePrivacy} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <label className="flex items-center gap-2">
            <input type="checkbox" name="share_data" defaultChecked={privacy?.share_data} /> Compartilhar dados
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" name="marketing_emails" defaultChecked={privacy?.marketing_emails} /> Marketing
          </label>
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Salvar</button>
        </form>
      </section>
    </div>
  );
}


