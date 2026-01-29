import monogram from '../assets/luisbank-monogram-clean.png';

type Props = {
  last4: string;
  bankName?: string;
  className?: string;
};

export function VisaBlackCard({ last4, bankName = 'LuisBank', className }: Props) {
  const W = 420;
  const H = 265;
  const R = 18;

  return (
    <div className={className}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%" style={{ display: 'block' }}>
        <defs>
          <linearGradient id="visa-black-base" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#0F172A" />
            <stop offset="100%" stopColor="#0B1220" />
          </linearGradient>
          <linearGradient id="visa-black-glow" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.04" />
            <stop offset="60%" stopColor="#ffffff" stopOpacity="0" />
            <stop offset="100%" stopColor="#ffffff" stopOpacity="0.06" />
          </linearGradient>
        </defs>

        <rect width={W} height={H} rx={R} fill="url(#visa-black-base)" />
        <rect width={W} height={H} rx={R} fill="url(#visa-black-glow)" />
        <rect x="0.75" y="0.75" width={W - 1.5} height={H - 1.5} rx={R} fill="transparent" stroke="#1f2937" strokeOpacity="0.6" />

        <g transform="translate(32,32)">
          <rect width="30" height="30" rx="6" fill="#0b1a12" />
          <image href={monogram} x="4" y="4" width="22" height="22" preserveAspectRatio="xMidYMid meet" />
        </g>
        <text x="72" y="52" fontSize="14" fontWeight="600" fill="#e2e8f0" fontFamily="ui-sans-serif, system-ui">
          {bankName}
        </text>
        <text x="32" y="78" fontSize="10" fontWeight="600" fill="#94a3b8" letterSpacing="1.4" fontFamily="ui-sans-serif, system-ui">
          VISA INFINITE
        </text>

        <g transform="translate(32,118)">
          <rect width="56" height="40" rx="8" fill="#1f2937" />
          <rect x="6" y="10" width="44" height="6" rx="3" fill="#475569" />
          <rect x="6" y="22" width="44" height="6" rx="3" fill="#475569" />
        </g>

        <text
          x="32"
          y="210"
          fontFamily="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
          fontSize="16"
          fontWeight="500"
          letterSpacing="1.4"
          fill="#e2e8f0"
        >
          XXXX XXXX XXXX {last4}
        </text>
        <text x="32" y="232" fontSize="9" fontWeight="600" fill="#94a3b8" letterSpacing="1.2" fontFamily="ui-sans-serif, system-ui">
          VIRTUAL
        </text>
        <text x="140" y="232" fontSize="9" fontWeight="600" fill="#94a3b8" letterSpacing="1.2" fontFamily="ui-sans-serif, system-ui">
          VAL 12/29
        </text>

        <text x="388" y="232" textAnchor="end" fontSize="14" fontWeight="700" fill="#cbd5e1" letterSpacing="1.2" fontFamily="ui-sans-serif, system-ui">
          VISA
        </text>
      </svg>
    </div>
  );
}
