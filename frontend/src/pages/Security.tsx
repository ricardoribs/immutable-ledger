import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Security() {
  const [devices, setDevices] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [mfaQr, setMfaQr] = useState<string | null>(null);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  async function loadData() {
    const [d, s, a, audit] = await Promise.all([
      api.get('/security/devices'),
      api.get('/security/sessions'),
      api.get('/security/alerts'),
      api.get('/security/audit'),
    ]);
    setDevices(d.data || []);
    setSessions(s.data || []);
    setAlerts(a.data || []);
    setAuditLogs(audit.data || []);
  }

  useEffect(() => {
    loadData().catch(() => {});
  }, []);

  async function revokeSession(id: number) {
    await api.post(`/security/sessions/${id}/revoke`, {});
    await loadData();
  }

  async function revokeDevice(id: number) {
    await api.post(`/security/devices/${id}/revoke`, {});
    await loadData();
  }

  async function handleOtp(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = { channel: String(form.get('channel')) };
    await api.post('/security/otp/request', payload);
    setLoading(false);
  }

  async function loadMfaQr() {
    const res = await api.get('/ledger/auth/mfa/qrcode');
    setMfaQr(res.data.qr_code_png_base64);
  }

  async function handleEnableMfa(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const code = String(form.get('code'));
    const res = await api.post(`/ledger/auth/mfa/enable?code=${code}`);
    setBackupCodes(res.data.backup_codes || []);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Segurança</h1>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Dispositivos</h2>
        <div className="space-y-2">
          {devices.map((d) => (
            <div key={d.id} className="flex justify-between border-b border-slate-100 pb-2">
              <span>{d.user_agent || 'Device'}</span>
              <button className="text-sm text-brand-primary" onClick={() => revokeDevice(d.id)}>Revogar</button>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Sessões</h2>
        <div className="space-y-2">
          {sessions.map((s) => (
            <div key={s.id} className="flex justify-between border-b border-slate-100 pb-2">
              <span>{s.jti}</span>
              <button className="text-sm text-brand-primary" onClick={() => revokeSession(s.id)}>Encerrar</button>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Alertas</h2>
        <div className="space-y-2">
          {alerts.map((a) => (
            <div key={a.id} className="flex justify-between border-b border-slate-100 pb-2">
              <span>{a.alert_type}</span>
              <span className="text-xs text-gray-500">{a.created_at}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Audit log</h2>
        <div className="space-y-2">
          {auditLogs.map((log) => (
            <div key={log.id} className="flex flex-wrap justify-between border-b border-slate-100 pb-2 text-sm">
              <span>{log.action}</span>
              <span className="text-slate-500">{log.ip_address}</span>
              <span className="text-slate-500">{log.user_agent}</span>
              <span className="text-slate-500">{log.timestamp}</span>
            </div>
          ))}
          {auditLogs.length === 0 && <div className="text-sm text-slate-500">Sem eventos recentes.</div>}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Token por SMS/Email</h2>
        <form onSubmit={handleOtp} className="flex gap-2">
          <select name="channel" className="border p-2 rounded">
            <option value="sms">SMS</option>
            <option value="email">Email</option>
            <option value="push">Push</option>
          </select>
          <button disabled={loading} className="bg-brand-primary text-white px-4 rounded">Gerar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="font-semibold">MFA (Google Authenticator)</h2>
            <div className="text-xs text-slate-500">Obrigatório para transações acima de R$ 1.000.</div>
          </div>
          <button onClick={loadMfaQr} className="text-sm text-brand-primary">Gerar QR Code</button>
        </div>
        {mfaQr && (
          <div className="mt-4 flex flex-col md:flex-row gap-4 items-center">
            <img src={`data:image/png;base64,${mfaQr}`} alt="QR Code MFA" className="w-40 h-40 border rounded" />
            <form onSubmit={handleEnableMfa} className="flex gap-2">
              <input name="code" placeholder="Código 6 dígitos" className="border p-2 rounded" />
              <button className="bg-brand-dark text-white px-4 rounded">Ativar MFA</button>
            </form>
          </div>
        )}
        {backupCodes.length > 0 && (
          <div className="mt-4 text-sm text-slate-700">
            <div className="font-semibold mb-2">Códigos de backup:</div>
            <div className="flex flex-wrap gap-2">
              {backupCodes.map((code) => (
                <span key={code} className="px-2 py-1 rounded bg-brand-light border">{code}</span>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

