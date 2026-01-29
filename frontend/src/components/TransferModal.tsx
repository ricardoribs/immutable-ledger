import { useState } from 'react';
import { useForm } from 'react-hook-form';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';
import { X, ArrowRight, Check, Shield, AlertCircle } from 'lucide-react';

interface TransferModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  currentBalance: number;
}

function generateUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export default function TransferModal({ isOpen, onClose, onSuccess, currentBalance }: TransferModalProps) {
  const { register, handleSubmit, reset, watch } = useForm();
  const user = useAuthStore((s) => s.user);

  const [step, setStep] = useState<'FORM' | 'MFA' | 'SUCCESS'>('FORM');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mfaPayload, setMfaPayload] = useState<any>(null);

  const amountValue = watch('amount');

  if (!isOpen) return null;

  const formatCurrency = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  const extractError = (err: any) => {
    try {
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (Array.isArray(detail)) {
          return detail.map((e: any) => {
            const field = e.loc ? e.loc[e.loc.length - 1] : 'Campo';
            return `${field}: ${e.msg}`;
          }).join(' | ');
        }
        return JSON.stringify(detail);
      }
      return 'Erro desconhecido.';
    } catch (e) {
      return 'Erro interno.';
    }
  };

  const onSubmit = async (data: any) => {
    setLoading(true);
    setError('');

    try {
      const rawAmount = Number(data.amount);
      const toAccountId = Number(data.to_account_id);

      if (!rawAmount || rawAmount <= 0) throw new Error('Valor inválido.');
      if (rawAmount > currentBalance) throw new Error('Saldo insuficiente.');
      if (!toAccountId) throw new Error('Conta de destino inválida.');
      if (!user?.id) throw new Error('Erro de sessão. Faça login novamente.');

      const payload = {
        amount: rawAmount,
        to_account_id: toAccountId,
        from_account_id: user.id,
        description: data.description || 'Transferência App',
        idempotency_key: generateUUID()
      };

      const finalPayload = (step === 'MFA' && mfaPayload) ? mfaPayload : payload;
      const params = data.otp ? { otp: data.otp } : {};

      await api.post('/ledger/transfers', finalPayload, { params });

      setStep('SUCCESS');
      setTimeout(() => {
        onSuccess();
        handleClose();
      }, 2000);

    } catch (err: any) {
      const msg = extractError(err);

      if (err.response?.status === 401 && String(msg).includes('MFA')) {
        const payloadToSave = {
          amount: Number(data.amount),
          to_account_id: Number(data.to_account_id),
          from_account_id: user?.id,
          description: data.description || 'Transferência App',
          idempotency_key: generateUUID()
        };
        setMfaPayload(payloadToSave);
        setStep('MFA');
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(String(msg));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    reset();
    setStep('FORM');
    setMfaPayload(null);
    setError('');
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="lb-surface w-full max-w-md rounded-3xl overflow-hidden">
        <div className="bg-brand-dark p-4 flex justify-between items-center text-white">
          <h3 className="font-bold">Transferir</h3>
          <button onClick={handleClose} className="hover:bg-white/10 p-1 rounded"><X size={20} /></button>
        </div>

        <div className="p-6">
          {step === 'SUCCESS' ? (
            <div className="text-center py-8 space-y-4">
              <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto">
                <Check size={32} />
              </div>
              <h2 className="text-xl font-bold text-gray-800">Sucesso!</h2>
              <p className="text-gray-500">Transferência concluída.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
              {error && (
                <div className="p-3 bg-red-50 text-red-700 text-xs font-mono rounded-lg border border-red-200 flex items-start gap-2 break-all">
                  <AlertCircle size={16} className="mt-0.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {step === 'FORM' && (
                <>
                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Conta destino (ID)</label>
                    <input
                      {...register('to_account_id')}
                      type="number"
                      required
                      placeholder="Ex: 2"
                      className="w-full p-3 border rounded-lg bg-gray-50 focus:ring-2 focus:ring-brand-primary outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Valor (R$)</label>
                    <div className="relative">
                      <span className="absolute left-3 top-3 text-gray-400 font-bold">R$</span>
                      <input
                        {...register('amount')}
                        type="number"
                        step="0.01"
                        required
                        placeholder="0.00"
                        className="w-full p-3 pl-10 border rounded-lg text-xl font-bold text-brand-dark focus:ring-2 focus:ring-brand-primary outline-none"
                      />
                    </div>
                    <div className="flex justify-between items-center mt-2 text-xs">
                      <span className="text-gray-500">Disponível:</span>
                      <span className={`font-bold ${Number(amountValue) > currentBalance ? 'text-red-500' : 'text-brand-primary'}`}>
                        {formatCurrency(currentBalance)}
                      </span>
                    </div>
                  </div>
                </>
              )}

              {step === 'MFA' && (
                <div className="space-y-4">
                  <div className="bg-yellow-50 p-4 rounded-lg flex gap-3 border border-yellow-200">
                    <Shield className="text-yellow-600 shrink-0" />
                    <div>
                      <p className="font-bold text-yellow-800 text-sm">Autenticação reforçada</p>
                      <p className="text-xs text-yellow-700">Valor alto. Confirme com seu 2FA.</p>
                    </div>
                  </div>
                  <input
                    {...register('otp')}
                    autoFocus
                    placeholder="000000"
                    className="w-full p-3 text-center text-2xl font-mono tracking-widest border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-primary outline-none"
                  />
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-brand-primary hover:bg-brand-dark text-white p-4 rounded-xl font-bold flex items-center justify-center gap-2 mt-4 shadow-lg transition-all"
              >
                {loading ? 'Processando...' : (step === 'FORM' ? 'Continuar' : 'Confirmar')}
                {!loading && <ArrowRight size={18} />}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}


