import React from 'react';
import monogramSvg from '../assets/luisbank-monogram.svg?raw';

type Props = {
  size?: 'sm' | 'md' | 'lg';
  subtitle?: string;
};

export function LuisBankLogo({ size = 'md', subtitle = 'Banco tradicional, visão digital' }: Props) {
  const scale =
    size === 'sm' ? { icon: 34, word: 'text-xl', sub: 'text-[11px]' } :
    size === 'lg' ? { icon: 54, word: 'text-3xl', sub: 'text-sm' } :
      { icon: 42, word: 'text-2xl', sub: 'text-xs' };

  return (
    <div className="flex items-center gap-3">
      <div className="rounded-sm border border-white/10 bg-white/5 p-2 lb-logo-inline" style={{ width: scale.icon, height: scale.icon }}>
        <span className="sr-only">LuisBank</span>
        <div dangerouslySetInnerHTML={{ __html: monogramSvg }} />
      </div>
      <div className="leading-tight">
        <div className={`${scale.word} font-semibold tracking-tight`}>
          <span className="gold-text gold-3d gold-stroke">LuisBank</span>
        </div>
        <div className={`${scale.sub} text-white/70`}>{subtitle}</div>
      </div>
    </div>
  );
}
