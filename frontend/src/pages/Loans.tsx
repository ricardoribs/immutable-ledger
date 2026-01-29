import { useEffect, useState } from 'react';
import api from '../services/api';

export default function Loans() {
  const [simulation, setSimulation] = useState<any>(null);
  const [loans, setLoans] = useState<any[]>([]);
  const [installments, setInstallments] = useState<any[]>([]);
  const [selectedLoanId, setSelectedLoanId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadLoans() {
    const res = await api.get('/loans');
    const items = res.data || [];
    setLoans(items);
    if (items.length > 0 && !selectedLoanId) {
      setSelectedLoanId(items[0].id);
    }
  }

  async function loadInstallments(loanId: number) {
    const res = await api.get(`/loans/${loanId}/installments`);
    setInstallments(res.data || []);
  }

  useEffect(() => {
    loadLoans().catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedLoanId) {
      loadInstallments(selectedLoanId).catch(() => {});
    }
  }, [selectedLoanId]);

  async function handleSimulate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = {
      principal: Number(form.get('principal')),
      rate_monthly: Number(form.get('rate')),
      term_months: Number(form.get('term')),
      amortization_type: String(form.get('amortization_type')),
    };
    const res = await api.post('/loans/simulate', payload);
    setSimulation(res.data);
  }

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      account_id: Number(form.get('account_id')),
      loan_type: String(form.get('loan_type')),
      principal: Number(form.get('principal')),
      rate_monthly: Number(form.get('rate')),
      term_months: Number(form.get('term')),
      amortization_type: String(form.get('amortization_type')),
    };
    await api.post('/loans', payload);
    await loadLoans();
    setLoading(false);
    e.currentTarget.reset();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Empréstimos</h1>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Simular</h2>
        <form onSubmit={handleSimulate} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="principal" required placeholder="Valor" className="border p-2 rounded" />
          <input name="rate" required placeholder="Taxa mensal (ex: 0,02)" className="border p-2 rounded" />
          <input name="term" required placeholder="Prazo (meses)" className="border p-2 rounded" />
          <select name="amortization_type" className="border p-2 rounded">
            <option value="PRICE">Price</option>
            <option value="SAC">SAC</option>
          </select>
          <button className="bg-brand-primary text-white py-2 rounded">Simular</button>
        </form>
        {simulation && (
          <div className="mt-4 text-sm">
            Parcela: R$ {Number(simulation.installment_amount).toFixed(2)} | Total: R$ {Number(simulation.total_payable).toFixed(2)}
          </div>
        )}
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Contratar</h2>
        <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="account_id" required placeholder="Conta ID" className="border p-2 rounded" />
          <select name="loan_type" className="border p-2 rounded">
            <option value="PERSONAL">Pessoal</option>
            <option value="CONSIGNADO">Consignado</option>
            <option value="VEHICLE">Veículo</option>
            <option value="HOME">Imobiliário</option>
          </select>
          <input name="principal" required placeholder="Valor" className="border p-2 rounded" />
          <input name="rate" required placeholder="Taxa mensal" className="border p-2 rounded" />
          <input name="term" required placeholder="Prazo" className="border p-2 rounded" />
          <select name="amortization_type" className="border p-2 rounded">
            <option value="PRICE">Price</option>
            <option value="SAC">SAC</option>
          </select>
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Contratar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Meus contratos</h2>
        <div className="space-y-2">
          {loans.map((l) => (
            <div key={l.id} className="flex flex-wrap justify-between border-b border-slate-100 pb-2 text-sm">
              <button className="text-brand-primary" onClick={() => setSelectedLoanId(l.id)}>Contrato #{l.id}</button>
              <span>R$ {Number(l.principal).toFixed(2)}</span>
              <span>{l.status}</span>
              <span>Score {l.credit_score}</span>
              <span>IOF R$ {Number(l.iof_amount).toFixed(2)}</span>
            </div>
          ))}
          {loans.length === 0 && <div className="text-sm text-slate-500">Nenhum empréstimo ativo.</div>}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Parcelas</h2>
        <div className="space-y-2">
          {installments.map((i) => (
            <div key={i.id} className="flex justify-between border-b border-slate-100 pb-2 text-sm">
              <span>Parcela #{i.id}</span>
              <span>R$ {Number(i.amount).toFixed(2)}</span>
              <span>{i.paid ? 'Pago' : 'Em aberto'}</span>
            </div>
          ))}
          {installments.length === 0 && <div className="text-sm text-slate-500">Selecione um contrato.</div>}
        </div>
      </section>
    </div>
  );
}

