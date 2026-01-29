
import { useEffect, useMemo, useState } from 'react';
import api from '../services/api';
import { useAuthStore } from '../store/authStore';
import { PhotoRealMetalCard } from '../components/PhotoRealMetalCard';
import { VisaInfiniteSilver_1to1 } from '../components/VisaInfiniteSilver_1to1';
import { VisaBlackCard } from '../components/VisaBlackCard';

interface Card {
  id: number;
  card_type: string;
  last4: string;
  status: string;
  limit_total: number;
  limit_available: number;
  card_token?: string | null;
  international_enabled: boolean;
  online_enabled: boolean;
  contactless_enabled: boolean;
  created_at?: string;
}

type CardStyle = {
  type: string;
  label: string;
  brand: 'VISA' | 'Mastercard' | 'Elo' | 'Amex';
  variant: 'silver' | 'gold' | 'titanium' | 'copper' | 'green' | 'black';
  limit: number;
};

const virtualCardStyles: CardStyle[] = [
  {
    type: 'VIRTUAL_SILVER',
    label: 'Visa Infinite',
    brand: 'VISA',
    variant: 'silver',
    limit: 8000,
  },
  {
    type: 'VIRTUAL_BLACK',
    label: 'Visa Infinite',
    brand: 'VISA',
    variant: 'black',
    limit: 15000,
  },
  {
    type: 'VIRTUAL_TITANIUM',
    label: 'Elo Nanquim',
    brand: 'Elo',
    variant: 'titanium',
    limit: 10000,
  },
  {
    type: 'VIRTUAL_ROSE',
    label: 'Elo Nanquim',
    brand: 'Elo',
    variant: 'copper',
    limit: 12000,
  },
  {
    type: 'VIRTUAL_GREEN',
    label: 'Amex Platinum',
    brand: 'Amex',
    variant: 'green',
    limit: 20000,
  },
];

function hashToNumber(input: string, mod: number) {
  let hash = 0;
  for (let i = 0; i < input.length; i += 1) {
    hash = (hash * 31 + input.charCodeAt(i)) % mod;
  }
  return hash;
}

function buildExpiry(createdAt?: string) {
  const base = createdAt ? new Date(createdAt) : new Date();
  const month = String((base.getMonth() + 1) % 12 || 12).padStart(2, '0');
  const year = (base.getFullYear() + 3).toString().slice(-2);
  return `${month}/${year}`;
}

function buildCvc(card: Card) {
  const seed = `${card.card_token || ''}${card.last4}${card.card_type}`;
  const value = 100 + hashToNumber(seed, 900);
  return String(value).padStart(3, '0');
}

function formatMaskedPan(last4: string) {
  return `XXXX XXXX XXXX ${last4}`;
}

function getStyleForCard(card: Card) {
  const match = virtualCardStyles.find((item) => item.type === card.card_type);
  return match || virtualCardStyles[0];
}

function CardFace({
  card,
  onSelect,
}: {
  card: Card;
  onSelect?: () => void;
}) {
  const style = getStyleForCard(card);
  return (
    <button
      type="button"
      onClick={onSelect}
      className="relative w-full text-left"
    >
      {style.variant === 'black' ? (
        <div className="w-full max-w-[420px]">
          <VisaBlackCard last4={card.last4} bankName="LuisBank" />
        </div>
      ) : style.variant === 'silver' ? (
        <div className="w-full max-w-[420px]">
          <VisaInfiniteSilver_1to1 />
        </div>
      ) : (
        <PhotoRealMetalCard
          variant={style.variant}
          brand={style.brand}
          tier={style.label}
          last4={card.last4}
          bankName="LuisBank"
          className="w-full max-w-[420px]"
        />
      )}
    </button>
  );
}

export default function Cards() {
  const user = useAuthStore((s) => s.user);
  const [cards, setCards] = useState<Card[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [selectedCardId, setSelectedCardId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [seeded, setSeeded] = useState(false);
  const [showSensitive, setShowSensitive] = useState(false);

  const virtualCards = useMemo(
    () => cards.filter((card) => card.card_type.startsWith('VIRTUAL')),
    [cards]
  );

  const selectedCard = useMemo(
    () => cards.find((card) => card.id === selectedCardId) || virtualCards[0] || null,
    [cards, selectedCardId, virtualCards]
  );

  async function loadCards() {
    const res = await api.get('/cards');
    const items = res.data || [];
    setCards(items);
    if (items.length > 0 && !selectedCardId) {
      setSelectedCardId(items[0].id);
    }
  }

  async function loadCardDetails(cardId: number) {
    const [tx, inv] = await Promise.all([
      api.get(`/cards/${cardId}/transactions`),
      api.get(`/cards/${cardId}/invoices`),
    ]);
    setTransactions(tx.data || []);
    setInvoices(inv.data || []);
  }

  async function seedVirtualCards() {
    if (!user?.id || seeding) return;
    setSeeding(true);
    try {
      const existingTypes = new Set(virtualCards.map((card) => card.card_type));
      for (const style of virtualCardStyles) {
        if (existingTypes.has(style.type)) continue;
        await api.post('/cards', {
          account_id: user.id,
          card_type: style.type,
          limit_total: style.limit,
          due_day: 10,
          parent_card_id: null,
        });
      }
      await loadCards();
      setSeeded(true);
    } finally {
      setSeeding(false);
    }
  }

  useEffect(() => {
    loadCards().catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedCardId) {
      loadCardDetails(selectedCardId).catch(() => {});
    }
  }, [selectedCardId]);

  useEffect(() => {
    if (!seeded && user?.id && cards.length === 0) {
      seedVirtualCards().catch(() => {});
    }
  }, [seeded, user?.id, cards.length]);

  async function handleCreateCard(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      account_id: Number(form.get('account_id')) || Number(user?.id),
      card_type: String(form.get('card_type')),
      limit_total: Number(form.get('limit_total')),
      due_day: Number(form.get('due_day')),
      parent_card_id: form.get('parent_card_id') ? Number(form.get('parent_card_id')) : null,
    };
    await api.post('/cards', payload);
    await loadCards();
    setLoading(false);
    e.currentTarget.reset();
  }

  async function toggleBlock(card: Card) {
    const url = card.status === 'ACTIVE' ? `/cards/${card.id}/block` : `/cards/${card.id}/unblock`;
    await api.post(url, {});
    await loadCards();
  }

  async function handleControls(card: Card, updates: Partial<Card>) {
    const payload = {
      international_enabled: updates.international_enabled ?? card.international_enabled,
      online_enabled: updates.online_enabled ?? card.online_enabled,
      contactless_enabled: updates.contactless_enabled ?? card.contactless_enabled,
    };
    await api.post(`/cards/${card.id}/controls`, payload);
    await loadCards();
  }

  async function handleCreateTransaction(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    const form = new FormData(e.currentTarget);
    const payload = {
      card_id: Number(form.get('card_id')),
      amount: Number(form.get('amount')),
      merchant: String(form.get('merchant') || ''),
      channel: String(form.get('channel')),
      description: String(form.get('description') || ''),
    };
    await api.post('/cards/transactions', payload);
    if (payload.card_id) {
      await loadCardDetails(payload.card_id);
    }
    setLoading(false);
    e.currentTarget.reset();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-brand-dark">Cartões</h1>

      <section className="lb-card lb-card-info p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div className="lb-label">Cartões</div>
            <h2 className="text-lg font-semibold text-brand-dark">Cartões virtuais LuisBank</h2>
            <p className="text-sm text-slate-500">
              Cartões virtuais ativos para uso online.
            </p>
          </div>
          <button
            type="button"
            onClick={() => seedVirtualCards()}
            disabled={seeding || !user?.id}
            className="lb-action-btn lb-btn-primary disabled:opacity-60"
          >
            {seeding ? 'Gerando...' : 'Gerar cartões virtuais'}
          </button>
        </div>
        <div className="mt-5 grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-6 items-start">
          <div className="space-y-3">
            <div className="lb-label">Cartão principal</div>
            <CardFace card={selectedCard || {
              id: -1,
              card_type: virtualCardStyles[0].type,
              last4: '0000',
              status: 'ACTIVE',
              limit_total: virtualCardStyles[0].limit,
              limit_available: virtualCardStyles[0].limit,
              international_enabled: true,
              online_enabled: true,
              contactless_enabled: true,
            } as Card} />
          </div>
          <div className="space-y-3">
            <div className="lb-label">Outros cartões</div>
            <div className="space-y-2">
              {(virtualCards.length ? virtualCards : virtualCardStyles.map((item, index) => ({
                id: -1 - index,
                card_type: item.type,
                last4: '0000',
                status: 'ACTIVE',
                limit_total: item.limit,
                limit_available: item.limit,
                international_enabled: true,
                online_enabled: true,
                contactless_enabled: true,
              } as Card))).filter((card) => card.id !== selectedCard?.id).map((card) => {
                const style = getStyleForCard(card);
                return (
                  <button
                    key={card.id}
                    type="button"
                    onClick={card.id > 0 ? () => setSelectedCardId(card.id) : undefined}
                    className="w-full border border-slate-200 rounded-sm px-4 py-3 text-left flex items-center justify-between bg-white hover:border-slate-300"
                  >
                    <div>
                      <div className="text-xs uppercase tracking-[0.16em] text-slate-500">LuisBank</div>
                      <div className="text-sm font-semibold text-slate-900">{style.label}</div>
                      <div className="text-xs text-slate-500 mt-1">{formatMaskedPan(card.last4)}</div>
                    </div>
                    <div className="text-xs text-slate-500">{buildExpiry(card.created_at)}</div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {selectedCard && (
        <section className="lb-card lb-card-info p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="lb-label">Detalhes</div>
              <h2 className="text-lg font-semibold text-brand-dark">Gestão do cartão virtual</h2>
              <p className="text-sm text-slate-500">Acesso controlado a dados sensíveis e limites.</p>
            </div>
            <button
              type="button"
              onClick={() => setShowSensitive((prev) => !prev)}
              className="lb-action-btn lb-btn-ghost"
            >
              {showSensitive ? 'Ocultar dados' : 'Mostrar dados'}
            </button>
          </div>
          <div className="mt-5 grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-6 items-start">
            <div className="relative">
              <CardFace card={selectedCard} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="border border-slate-200 rounded-sm p-4">
                <div className="lb-label">Número do cartão</div>
                <div className="text-base font-medium text-slate-900 mt-2">
                  {showSensitive ? formatMaskedPan(selectedCard.last4) : 'XXXX XXXX XXXX XXXX'}
                </div>
              </div>
              <div className="border border-slate-200 rounded-sm p-4">
                <div className="lb-label">CVC</div>
                <div className="text-base font-medium text-slate-900 mt-2">
                  {showSensitive ? buildCvc(selectedCard) : 'XXX'}
                </div>
              </div>
              <div className="border border-slate-200 rounded-sm p-4">
                <div className="lb-label">Limite total</div>
                <div className="text-base font-medium text-slate-900 mt-2">R$ {Number(selectedCard.limit_total).toFixed(2)}</div>
              </div>
              <div className="border border-slate-200 rounded-sm p-4">
                <div className="lb-label">Limite disponível</div>
                <div className="text-base font-medium text-slate-900 mt-2">R$ {Number(selectedCard.limit_available).toFixed(2)}</div>
              </div>
            </div>
          </div>
        </section>
      )}

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Novo Cartão</h2>
        <form onSubmit={handleCreateCard} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input
            name="account_id"
            required
            placeholder="Conta ID"
            defaultValue={user?.id || ''}
            className="border p-2 rounded"
          />
          <select name="card_type" className="border p-2 rounded">
            <option value="DEBIT">Débito</option>
            <option value="CREDIT">Crédito</option>
            <option value="VIRTUAL">Virtual</option>
          </select>
          <input name="limit_total" required placeholder="Limite" className="border p-2 rounded" />
          <input name="due_day" placeholder="Vencimento (dia)" className="border p-2 rounded" />
          <input name="parent_card_id" placeholder="Cartão base (virtual)" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Criar</button>
        </form>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Meus Cartões</h2>
        <div className="space-y-3">
          {cards.map((c) => (
            <div key={c.id} className="border border-slate-100 rounded-xl p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="font-semibold">{c.card_type} • **** {c.last4}</div>
                  <div className="text-xs text-slate-500">Limite disponível: R$ {Number(c.limit_available).toFixed(2)}</div>
                  {c.card_token && <div className="text-xs text-slate-500">Token: {c.card_token}</div>}
                </div>
                <div className="flex gap-2">
                  <button className="text-sm text-brand-primary" onClick={() => setSelectedCardId(c.id)}>Detalhes</button>
                  <button className="text-sm text-brand-primary" onClick={() => toggleBlock(c)}>
                    {c.status === 'ACTIVE' ? 'Bloquear' : 'Desbloquear'}
                  </button>
                </div>
              </div>
              <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-2 text-sm">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={c.online_enabled}
                    onChange={(e) => handleControls(c, { online_enabled: e.target.checked })}
                  />
                  Compras online
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={c.international_enabled}
                    onChange={(e) => handleControls(c, { international_enabled: e.target.checked })}
                  />
                  Compras internacionais
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={c.contactless_enabled}
                    onChange={(e) => handleControls(c, { contactless_enabled: e.target.checked })}
                  />
                  Aproximação (contactless)
                </label>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Transações do Cartão</h2>
        <form onSubmit={handleCreateTransaction} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input name="card_id" required placeholder="Cartão ID" className="border p-2 rounded" defaultValue={selectedCardId || ''} />
          <input name="amount" required placeholder="Valor" className="border p-2 rounded" />
          <input name="merchant" placeholder="Estabelecimento" className="border p-2 rounded" />
          <select name="channel" className="border p-2 rounded">
            <option value="ONLINE">Online</option>
            <option value="IN_PERSON">Presencial</option>
            <option value="CONTACTLESS">Aproximação</option>
          </select>
          <input name="description" placeholder="Descrição" className="border p-2 rounded" />
          <button disabled={loading} className="bg-brand-primary text-white py-2 rounded">Registrar</button>
        </form>
        <div className="mt-4 space-y-2">
          {transactions.map((t) => (
            <div key={t.id} className="flex justify-between border-b border-slate-100 pb-2 text-sm">
              <span>{t.merchant || 'Compra'}</span>
              <span>R$ {Number(t.amount).toFixed(2)}</span>
              <span>{t.status}</span>
            </div>
          ))}
          {transactions.length === 0 && <div className="text-sm text-slate-500">Sem Transações.</div>}
        </div>
      </section>

      <section className="lb-card lb-card-info p-4">
        <h2 className="font-semibold mb-3">Faturas</h2>
        <div className="space-y-2">
          {invoices.map((i) => (
            <div key={i.id} className="flex justify-between border-b border-slate-100 pb-2 text-sm">
              <span>Fatura #{i.id}</span>
              <span>R$ {Number(i.total).toFixed(2)}</span>
              <span>{i.status}</span>
            </div>
          ))}
          {invoices.length === 0 && <div className="text-sm text-slate-500">Sem faturas.</div>}
        </div>
      </section>
    </div>
  );
}


