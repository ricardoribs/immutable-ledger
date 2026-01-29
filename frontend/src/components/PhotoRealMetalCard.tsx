import React from "react";

type Variant = "silver" | "gold" | "titanium" | "copper" | "green";
type Brand = "VISA" | "Mastercard" | "Elo" | "Amex";

type Props = {
  variant: Variant;
  brand: Brand;
  tier: string;
  last4: string;
  bankName?: string;
  className?: string;
};

const PALETTE: Record<
  Variant,
  {
    base1: string;
    base2: string;
    base3: string;
    edge: string;
    ink: string;
    ink2: string;
    accent: string;
    mono?: string;
  }
> = {
  silver: {
    base1: "#F4F6F8",
    base2: "#C7D0DA",
    base3: "#8E99A6",
    edge: "#AAB3BE",
    ink: "#0F172A",
    ink2: "#334155",
    accent: "#1F7A4A",
  },
  gold: {
    base1: "#F7EDC9",
    base2: "#D7B24B",
    base3: "#8B6A16",
    edge: "#B6902A",
    ink: "#1A1206",
    ink2: "#3B2E16",
    accent: "#1F7A4A",
  },
  titanium: {
    base1: "#EEF2F7",
    base2: "#A1ACBA",
    base3: "#5E6A79",
    edge: "#7C8796",
    ink: "#0B1220",
    ink2: "#334155",
    accent: "#1F7A4A",
  },
  copper: {
    base1: "#F0BCA6",
    base2: "#A76441",
    base3: "#5B2B17",
    edge: "#7E4226",
    ink: "#1A0E0A",
    ink2: "#3B1F16",
    accent: "#1F7A4A",
  },
  green: {
    base1: "#0F2A1F",
    base2: "#081A13",
    base3: "#04110C",
    edge: "#0B3B2A",
    ink: "#ECFDF5",
    ink2: "#CFFAE3",
    accent: "#1F7A4A",
    mono: "#D6B55C",
  },
};

function brandLabel(b: Brand) {
  if (b === "Mastercard") return "mastercard";
  if (b === "Amex") return "AMERICAN EXPRESS";
  if (b === "Elo") return "elo";
  return "VISA";
}

export function PhotoRealMetalCard({
  variant,
  brand,
  tier,
  last4,
  bankName = "LuisBank",
  className,
}: Props) {
  const p = PALETTE[variant];

  const W = 420;
  const H = 265;
  const R = 18;

  const id = React.useId();
  const clip = `clip-${id}`;
  const metal = `metal-${id}`;
  const brush = `brush-${id}`;
  const spec = `spec-${id}`;
  const vign = `vign-${id}`;
  const grain = `grain-${id}`;
  const emboss = `emboss-${id}`;
  const chipGrad = `chip-${id}`;

  return (
    <div className={className}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%" style={{ display: "block" }}>
        <defs>
          <clipPath id={clip}>
            <rect x="0" y="0" width={W} height={H} rx={R} ry={R} />
          </clipPath>

          <linearGradient id={metal} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor={p.base1} />
            <stop offset="0.45" stopColor={p.base2} />
            <stop offset="1" stopColor={p.base3} />
          </linearGradient>

          <pattern
            id={brush}
            width="5"
            height="5"
            patternUnits="userSpaceOnUse"
            patternTransform="rotate(-18)"
          >
            <rect width="5" height="5" fill="transparent" />
            <rect x="0" width="1" height="5" fill="#fff" opacity={variant === "green" ? 0.06 : 0.08} />
            <rect x="2.5" width="1" height="5" fill="#000" opacity={variant === "green" ? 0.04 : 0.06} />
          </pattern>

          <linearGradient id={spec} x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#ffffff" stopOpacity="0" />
            <stop offset="0.22" stopColor="#ffffff" stopOpacity="0.05" />
            <stop offset="0.38" stopColor="#ffffff" stopOpacity={variant === "green" ? 0.10 : 0.16} />
            <stop offset="0.52" stopColor="#ffffff" stopOpacity="0.06" />
            <stop offset="0.68" stopColor="#ffffff" stopOpacity="0" />
            <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
          </linearGradient>

          <radialGradient id={vign} cx="35%" cy="20%" r="95%">
            <stop offset="0" stopColor="#000" stopOpacity="0" />
            <stop offset="0.55" stopColor="#000" stopOpacity="0" />
            <stop offset="1" stopColor="#000" stopOpacity={variant === "green" ? 0.35 : 0.22} />
          </radialGradient>

          <filter id={grain} x="-20%" y="-20%" width="140%" height="140%">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" result="n" />
            <feColorMatrix
              in="n"
              type="matrix"
              values="
                1 0 0 0 0
                0 1 0 0 0
                0 0 1 0 0
                0 0 0 .14 0"
              result="na"
            />
            <feBlend in="SourceGraphic" in2="na" mode="overlay" />
          </filter>

          <filter id={emboss} x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur in="SourceAlpha" stdDeviation="0.9" result="blur" />
            <feOffset in="blur" dx="1.2" dy="1.2" result="shadow" />
            <feOffset in="blur" dx="-0.9" dy="-0.9" result="light" />
            <feColorMatrix
              in="shadow"
              type="matrix"
              values="
                0 0 0 0 0
                0 0 0 0 0
                0 0 0 0 0
                0 0 0 .35 0"
              result="shadow2"
            />
            <feColorMatrix
              in="light"
              type="matrix"
              values="
                1 0 0 0 1
                0 1 0 0 1
                0 0 1 0 1
                0 0 0 .22 0"
              result="light2"
            />
            <feMerge>
              <feMergeNode in="shadow2" />
              <feMergeNode in="light2" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          <linearGradient id={chipGrad} x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor={variant === "green" ? "#E5D18D" : "#E5EAF0"} />
            <stop offset="0.45" stopColor={variant === "green" ? "#B89E55" : "#B9C2CC"} />
            <stop offset="1" stopColor={variant === "green" ? "#7A6232" : "#7B8794"} />
          </linearGradient>
        </defs>

        <g clipPath={`url(#${clip})`} filter={`url(#${grain})`}>
          <rect width={W} height={H} fill={`url(#${metal})`} />
          <rect width={W} height={H} fill={`url(#${brush})`} opacity={variant === "green" ? 0.10 : 0.16} />

          <g transform="translate(-40,0) rotate(-8 210 132)">
            <rect x="0" y="0" width={W + 80} height={H} fill={`url(#${spec})`} opacity={0.95} />
          </g>

          <rect width={W} height={H} fill={`url(#${vign})`} />

          <rect
            x="0.75"
            y="0.75"
            width={W - 1.5}
            height={H - 1.5}
            rx={R}
            ry={R}
            fill="transparent"
            stroke={p.edge}
            strokeOpacity={0.65}
          />

          <g transform="translate(28,34)">
            <g transform="rotate(90)">
              <rect x="-6" y="-18" width="22" height="22" rx="5" fill={p.accent} opacity={0.9} />
              <text
                x="28"
                y="0"
                fill={p.ink}
                fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto"
                fontSize="18"
                fontWeight={800}
                opacity={0.92}
              >
                {bankName}
              </text>
            </g>
          </g>

          <g transform="translate(50,34)">
            <text
              x="0"
              y="0"
              fill={p.ink2}
              fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto"
              fontSize="18"
              fontWeight={900}
              letterSpacing="1.0"
              opacity={variant === "green" ? 0.9 : 0.85}
            >
              {brand === "VISA" ? "VISA" : brand === "Elo" ? "ELO" : brand === "Amex" ? "AMEX" : "MC"}
            </text>
            <text
              x="0"
              y="18"
              fill={p.ink2}
              fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto"
              fontSize="12"
              fontWeight={700}
              letterSpacing="1.4"
              opacity={0.65}
            >
              {tier}
            </text>
          </g>

          <g transform="translate(172,150)">
            <rect x="0" y="0" width="60" height="44" rx="10" fill={`url(#${chipGrad})`} opacity="0.98" />
            <rect x="7" y="10" width="46" height="6" rx="3" fill="#0B1220" opacity="0.12" />
            <rect x="7" y="20" width="46" height="6" rx="3" fill="#0B1220" opacity="0.10" />
            <rect x="7" y="30" width="46" height="6" rx="3" fill="#0B1220" opacity="0.08" />
          </g>

          <g transform={`translate(${W - 56}, 78) rotate(90)`} filter={`url(#${emboss})`}>
            <text
              x="0"
              y="0"
              fill={variant === "green" ? "#D6B55C" : p.ink2}
              fontFamily='ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace'
              fontSize="18"
              fontWeight={800}
              letterSpacing="2.6"
              opacity={variant === "green" ? 0.75 : 0.55}
            >
              1234 5678 9012 {last4}
            </text>
          </g>

          <g transform={`translate(${W - 22}, 38)`}>
            <text
              x="0"
              y="0"
              fill={p.ink2}
              fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto"
              fontSize={brand === "Amex" ? 10 : 12}
              fontWeight={brand === "Amex" ? 900 : 800}
              letterSpacing={brand === "Amex" ? 1.6 : 1.0}
              opacity={0.75}
              textAnchor="end"
            >
              {brandLabel(brand)}
            </text>
          </g>

          {variant === "green" && (
            <g transform="translate(300,160)">
              <text
                x="0"
                y="0"
                fill={PALETTE.green.mono}
                fontFamily="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto"
                fontSize="78"
                fontWeight={900}
                letterSpacing="-4"
                opacity={0.9}
              >
                LB
              </text>
            </g>
          )}
        </g>
      </svg>
    </div>
  );
}
