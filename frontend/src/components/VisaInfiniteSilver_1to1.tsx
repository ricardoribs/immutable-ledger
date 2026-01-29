export function VisaInfiniteSilver_1to1() {
  return (
    <svg
      viewBox="0 0 420 265"
      width="100%"
      height="100%"
      style={{ display: "block" }}
    >
      <defs>
        <linearGradient id="metal" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#E6EBF0" />
          <stop offset="55%" stopColor="#C8D0D8" />
          <stop offset="100%" stopColor="#AEB7C0" />
        </linearGradient>

        <pattern id="brush" width="3" height="3" patternUnits="userSpaceOnUse">
          <rect width="3" height="1" y="0" fill="#ffffff" opacity="0.04" />
          <rect width="3" height="1" y="2" fill="#000000" opacity="0.035" />
        </pattern>

        <linearGradient id="specular" x1="0" y1="0" x2="1" y2="0">
          <stop offset="55%" stopColor="#fff" stopOpacity="0" />
          <stop offset="70%" stopColor="#fff" stopOpacity="0.18" />
          <stop offset="82%" stopColor="#fff" stopOpacity="0.08" />
          <stop offset="100%" stopColor="#fff" stopOpacity="0" />
        </linearGradient>

        <radialGradient id="vignette" cx="50%" cy="50%" r="75%">
          <stop offset="60%" stopColor="#000" stopOpacity="0" />
          <stop offset="100%" stopColor="#000" stopOpacity="0.22" />
        </radialGradient>

        <filter id="emboss">
          <feOffset dx="1" dy="1" />
          <feGaussianBlur stdDeviation="0.8" />
          <feColorMatrix
            type="matrix"
            values="
              0 0 0 0 0
              0 0 0 0 0
              0 0 0 0 0
              0 0 0 .35 0"
          />
        </filter>
      </defs>

      <rect width="420" height="265" rx="18" fill="url(#metal)" />
      <rect width="420" height="265" rx="18" fill="url(#brush)" />
      <rect width="420" height="265" rx="18" fill="url(#specular)" />
      <rect width="420" height="265" rx="18" fill="url(#vignette)" />

      <g transform="translate(28,40) rotate(90)">
        <rect x="-6" y="-18" width="22" height="22" rx="4" fill="#1F7A4A" />
        <text
          x="28"
          y="0"
          fontSize="18"
          fontWeight="800"
          fill="#1F2937"
          fontFamily="system-ui"
        >
          LuisBank
        </text>
      </g>

      <text x="48" y="38" fontSize="18" fontWeight="800" fill="#374151">
        VISA
      </text>
      <text x="48" y="56" fontSize="12" fontWeight="600" fill="#6B7280">
        Visa Infinite
      </text>

      <g transform="translate(175,115)">
        <rect width="56" height="40" rx="8" fill="#C9D0D8" />
        <rect x="6" y="10" width="44" height="6" rx="3" fill="#9CA3AF" />
        <rect x="6" y="22" width="44" height="6" rx="3" fill="#9CA3AF" />
      </g>

      <g transform="translate(392,78) rotate(90)" filter="url(#emboss)">
        <text
          fontFamily="ui-monospace, monospace"
          fontSize="18"
          letterSpacing="3"
          fill="#4B5563"
          opacity="0.55"
        >
          1234 5678 9012
        </text>
      </g>

      <text
        x="380"
        y="36"
        textAnchor="end"
        fontSize="14"
        fontWeight="700"
        fill="#6B7280"
      >
        VISA
      </text>
    </svg>
  );
}
