import { useState } from 'react';
import { useForm } from 'react-hook-form';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';
import { X, QrCode, CheckCircle, ArrowDown, AlertCircle } from 'lucide-react';

interface PixModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
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

export default function PixModal({ isOpen, onClose, onSuccess }: PixModalProps) {
  const { register, handleSubmit, reset } = useForm();
  const user = useAuthStore((s) => s.user);

  const [step, setStep] = useState<'FORM' | 'QR' | 'SUCCESS'>('FORM');
  const [loading, setLoading] = useState(false);
  const [amount, setAmount] = useState(0);
  const [error, setError] = useState('');

  if (!isOpen) return null;

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
      return 'Erro ao processar Pix.';
    } catch (e) {
      return 'Erro interno.';
    }
  };

  const handleGenerateQR = (data: any) => {
    setAmount(Number(data.amount));
    setError('');
    setStep('QR');
  };

  const handleSimulatePayment = async () => {
    setLoading(true);
    setError('');

    try {
      if (!user?.id) throw new Error('Usuário não identificado.');

      const payload = {
        amount: amount,
        from_account_id: 1,
        to_account_id: user.id,
        description: 'Pix recebido',
        idempotency_key: generateUUID()
      };

      await api.post('/ledger/transfers', payload);

      setStep('SUCCESS');
      setTimeout(() => {
        onSuccess();
        handleClose();
      }, 2000);

    } catch (err: any) {
      const msg = extractError(err);
      if (msg.includes('Credenciais') || msg.includes('Forbidden')) {
        setError('Operação não autorizada. Verifique a conta de origem.');
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    reset();
    setStep('FORM');
    setLoading(false);
    setError('');
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="lb-surface w-full max-w-md rounded-3xl overflow-hidden">
        <div className="bg-brand-primary p-4 flex justify-between items-center text-white">
          <div className="flex items-center gap-2">
            <QrCode size={20} />
            <h3 className="font-bold">Área Pix</h3>
          </div>
          <button onClick={handleClose} className="hover:bg-white/10 p-1 rounded"><X size={20} /></button>
        </div>

        <div className="p-6">
          {step === 'SUCCESS' ? (
            <div className="text-center py-8 space-y-4">
              <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle size={32} />
              </div>
              <h2 className="text-xl font-bold text-gray-800">Pix recebido!</h2>
              <p className="text-gray-500">+ R$ {amount.toFixed(2)}</p>
            </div>
          ) : step === 'QR' ? (
            <div className="space-y-6 text-center">
              <h3 className="font-bold text-gray-700">Escaneie o QR Code</h3>

              {error && (
                <div className="p-3 bg-red-50 text-red-700 text-xs font-mono rounded-lg border border-red-200 flex items-start gap-2 text-left break-words">
                  <AlertCircle size={16} className="mt-0.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="w-48 h-48 bg-gray-100 mx-auto rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center relative overflow-hidden">
                <QrCode size={100} className="text-gray-400 opacity-20" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xs font-mono text-gray-500 bg-white px-2 py-1 rounded border">
                    00020126580014BR.GOV.BCB.PIX...
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-sm text-gray-500">Valor a receber: <span className="font-bold text-brand-dark">R$ {amount.toFixed(2)}</span></p>

                <button
                  onClick={handleSimulatePayment}
                  disabled={loading}
                  className="w-full bg-brand-primary hover:bg-brand-dark text-white p-4 rounded-xl font-bold flex items-center justify-center gap-2 shadow-lg transition"
                >
                  {loading ? 'Processando...' : 'Confirmar pagamento'}
                  {!loading && <ArrowDown size={18} />}
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit(handleGenerateQR)} className="space-y-5">
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase mb-1">Valor da cobrança (R$)</label>
                <input
                  {...register('amount')}
                  type="number"
                  step="0.01"
                  required
                  autoFocus
                  placeholder="0.00"
                  className="w-full p-4 text-center text-3xl font-bold text-brand-dark border rounded-xl focus:ring-2 focus:ring-brand-primary outline-none"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-brand-primary hover:bg-brand-dark text-white p-4 rounded-xl font-bold flex items-center justify-center gap-2 mt-4 shadow-lg transition-all"
              >
                Gerar cobrança
                <QrCode size={18} />
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

