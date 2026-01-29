import { useNavigate } from 'react-router-dom';
import heroImage from '../assets/luisbank-hero.png';
import logoGreen from '../assets/luisbank-logo-green.png';

const benefits = [
  'Operações rastreáveis com compliance contínuo',
  'Limites e segurança configuráveis em tempo real',
  'Atendimento humano 24h com histórico integrado',
];

const products = [
  { title: 'Conta corrente', icon: 'account' },
  { title: 'Cartão de crédito', icon: 'card' },
  { title: 'Pix', icon: 'pix' },
  { title: 'Empréstimos', icon: 'loan' },
  { title: 'Investimentos', icon: 'invest' },
  { title: 'Seguros', icon: 'shield' },
];

function ProductIcon({ name }: { name: string }) {
  switch (name) {
    case 'account':
      return (
        <svg viewBox="0 0 24 24" className="lb-service-icon" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="4" width="18" height="16" rx="1" />
          <path d="M7 8h10" />
          <path d="M7 12h6" />
          <path d="M7 16h8" />
        </svg>
      );
    case 'card':
      return (
        <svg viewBox="0 0 24 24" className="lb-service-icon" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <rect x="3" y="6" width="18" height="12" rx="1" />
          <path d="M3 10h18" />
          <path d="M7 14h6" />
        </svg>
      );
    case 'pix':
      return (
        <svg viewBox="0 0 24 24" className="lb-service-icon" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="M7 7h4l6 6-4 4-6-6V7Z" />
          <path d="M10 10h4" />
        </svg>
      );
    case 'loan':
      return (
        <svg viewBox="0 0 24 24" className="lb-service-icon" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 7h16" />
          <path d="M4 12h16" />
          <path d="M4 17h10" />
        </svg>
      );
    case 'invest':
      return (
        <svg viewBox="0 0 24 24" className="lb-service-icon" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 18h16" />
          <path d="M6 14l3-3 3 2 4-5" />
          <path d="M6 8h.01" />
        </svg>
      );
    case 'shield':
      return (
        <svg viewBox="0 0 24 24" className="lb-service-icon" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 3l7 4v5c0 4-3 7-7 9-4-2-7-5-7-9V7l7-4Z" />
          <path d="M12 9v6" />
          <path d="M9 12h6" />
        </svg>
      );
    default:
      return null;
  }
}

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen lb-hero-bg text-white">
      <header className="lb-fixed-header">
        <div className="max-w-6xl mx-auto px-6 py-6 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="lb-logo-green">
              <img src={logoGreen} alt="LuisBank" className="w-full h-full object-contain" />
            </div>
            <div>
              <div className="text-base font-semibold">LuisBank</div>
              <div className="text-[11px] text-white/70 font-medium">Banco tradicional, visão digital</div>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button type="button" className="lb-nav-pill">PF</button>
            <button type="button" className="lb-nav-pill lb-nav-pill-active">PJ</button>
            <button type="button" className="lb-nav-pill">Empresas</button>
          </div>

          <div className="flex items-center gap-2 flex-1 min-w-[240px] md:flex-none">
            <input
              className="lb-input"
              placeholder="Buscar produtos, serviços e canais"
              aria-label="Busca global"
            />
            <button type="button" className="lb-nav-pill" aria-label="Atalho de acessibilidade">
              Acessibilidade
            </button>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <a className="text-xs font-medium text-white/70 hover:text-white" href="#como-usar">Como usar</a>
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="lb-btn"
            >
              Acessar sua conta
            </button>
          </div>
        </div>

        <div className="max-w-6xl mx-auto px-6 pb-4 pt-2 hidden lg:flex items-center justify-between gap-4">
          <nav className="flex flex-wrap items-center gap-4 text-xs text-white/75">
            <a className="hover:text-white" href="#produtos">Produtos e serviços</a>
            <a className="hover:text-white" href="#abrir-conta">Abrir conta</a>
            <a className="hover:text-white" href="#contratar-online">Contratar online</a>
            <a className="hover:text-white" href="#atendimento">Atendimento</a>
            <a className="hover:text-white" href="#canais">Canais</a>
            <a className="hover:text-white" href="#educacao">Educação financeira</a>
            <a className="hover:text-white" href="#beneficios">Loja / Benefícios</a>
          </nav>
          <div className="flex items-center gap-2">
            <input className="lb-login-input" placeholder="Agência" aria-label="Agência" />
            <input className="lb-login-input" placeholder="Conta" aria-label="Conta" />
            <input className="lb-login-input" placeholder="Dígito" aria-label="Dígito" />
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="lb-btn"
            >
              Entrar
            </button>
          </div>
        </div>
      </header>

      <main className="pt-44 lg:pt-48 pb-10">
        <section className="max-w-6xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-[1.15fr_0.85fr] gap-8 items-start">
          <div className="space-y-4 lb-fade-up">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-sm bg-white/10 border border-white/25 text-[11px] font-semibold text-white/90">
              Portal bancário institucional
            </div>
            <h1 className="text-3xl md:text-4xl font-semibold leading-snug tracking-tight max-w-[32ch] font-sans">
              Gestão centralizada de contas, crédito e investimentos.
            </h1>
            <p className="text-white/80 max-w-[64ch] text-sm md:text-[15px] font-medium">
              Acesso multicanal integrado para pessoa física, PJ e empresas. Operações monitoradas, controles claros e governança contínua.
            </p>
            <ul className="space-y-2 text-sm">
              {benefits.map((item) => (
                <li key={item} className="flex items-start gap-3 text-white/80">
                  <span className="lb-icon-box lb-icon-box-light">
                    <svg viewBox="0 0 24 24" className="lb-icon" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M20 6L9 17l-5-5" />
                    </svg>
                  </span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="lb-btn"
              >
                Abrir conta
              </button>
              <button
                id="contratar-online"
                type="button"
                className="lb-btn lb-btn-secondary"
              >
                Contratar online
              </button>
            </div>
            <p className="text-[11px] text-white/55">*Sujeito à análise de crédito, validações cadastrais e políticas internas.</p>
            <p className="text-[11px] text-white/45">Informações preliminares. Consulte condições vigentes e tarifas oficiais.</p>
          </div>

          <div className="lb-surface lb-block lb-block-flat p-4 text-slate-900 lb-fade-up lb-fade-delay-2 lb-hero-card">
            <img
              src={heroImage}
              alt="Cliente usando o app do banco em um ambiente real"
              className="w-full h-auto object-contain lb-hero-photo"
            />
            <div className="mt-4">
              <div className="text-[11px] text-slate-600 font-semibold">Atendimento institucional</div>
              <div className="mt-2 text-base font-semibold text-brand-ink">Presença física e suporte direto</div>
              <div className="text-xs text-slate-600 mt-2">Equipe local, atendimento padronizado e orientação clara para clientes.</div>
            </div>
            <div className="mt-3 text-[11px] text-slate-500">*Imagem ilustrativa. Ambiente sujeito a alterações operacionais.</div>
            <div className="mt-2 text-[10px] text-slate-500">Condições de atendimento podem variar conforme unidade.</div>
          </div>
        </section>

        <section id="produtos" className="lb-band mt-5">
          <div className="max-w-6xl mx-auto px-6 py-5">
            <div className="flex items-center justify-between flex-wrap gap-3">
              <h2 className="text-xl font-semibold text-slate-900 font-sans">Produtos em destaque</h2>
              <button type="button" className="lb-nav-pill lb-nav-pill-light">Ver todos os produtos</button>
            </div>
            <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-4">
              {products.map((product) => (
                <div key={product.title} className="lb-service-card">
                  <ProductIcon name={product.icon} />
                  <div className="lb-service-title">{product.title}</div>
                </div>
              ))}
            </div>
            <div className="mt-3 text-[11px] text-slate-500">*Produtos sujeitos a análise cadastral e políticas de risco.</div>
            <div className="mt-1 text-[10px] text-slate-500">Consulte tarifas, limites e termos aplicáveis para cada produto.</div>
          </div>
        </section>

        <section id="abrir-conta" className="max-w-6xl mx-auto px-6 mt-5 grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-5 items-center">
          <div className="lb-surface lb-block lb-block-flat p-5 text-slate-900">
            <div className="text-[11px] text-slate-600 font-semibold">Abertura de conta digital</div>
            <h2 className="mt-2 text-xl font-semibold text-brand-ink font-sans">Cadastro rápido com validação automatizada</h2>
            <p className="text-sm text-slate-600 mt-2">
              Processo digital com checagem documental, antifraude e autenticação em duas etapas.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button type="button" className="px-3 py-1.5 rounded-sm bg-brand-dark text-white text-xs font-semibold">Abrir agora</button>
              <button type="button" className="px-3 py-1.5 rounded-sm border border-slate-200 text-xs font-medium">Falar com gerente</button>
            </div>
            <div className="mt-3 text-[11px] text-emerald-700 font-semibold">Ambiente protegido com criptografia e monitoramento 24h.</div>
            <div className="mt-1 text-[10px] text-slate-500">*Prazo de abertura sujeito à validação documental.</div>
          </div>
          <div className="lb-panel lb-block lb-block-flat p-5 text-slate-900">
            <div className="text-[11px] text-slate-600 font-semibold">Baixe o app</div>
            <div className="mt-3 flex items-center gap-5">
              <div className="w-28 h-28 border border-slate-200 bg-white flex items-center justify-center text-[11px] text-slate-400">QR Code</div>
              <div className="space-y-2">
                <button type="button" className="px-3 py-1.5 rounded-sm bg-brand-dark text-white text-[11px] font-semibold">App Store</button>
                <button type="button" className="px-3 py-1.5 rounded-sm border border-slate-200 text-[11px] font-medium">Google Play</button>
              </div>
            </div>
            <div className="mt-3 text-[11px] text-slate-600">Escaneie para baixar o app e continuar pelo celular.</div>
            <div className="mt-1 text-[10px] text-slate-500">Disponibilidade sujeita às políticas das lojas de aplicativos.</div>
          </div>
        </section>

        <section className="max-w-6xl mx-auto px-6 mt-5 grid grid-cols-1 lg:grid-cols-4 gap-3">
          {[
            { title: 'Atendimento 24h', desc: 'Equipe dedicada com histórico completo.' },
            { title: 'Assistente virtual', desc: 'Respostas imediatas com escalonamento humano.' },
            { title: 'Segurança e criptografia', desc: 'Proteção multicamada em todas as transações.' },
            { title: 'Governança e compliance', desc: 'Auditoria contínua e processos transparentes.' },
          ].map((item) => (
            <div key={item.title} className="lb-panel lb-block lb-block-flat p-3 text-slate-900">
              <div className="text-xs font-semibold text-brand-ink">{item.title}</div>
              <div className="text-[11px] text-slate-600 mt-2">{item.desc}</div>
            </div>
          ))}
          <div className="lg:col-span-4 text-[11px] text-slate-500">
            Avisos legais: crédito sujeito à aprovação e análise cadastral. Consulte condições vigentes, tarifas e política de privacidade.
          </div>
          <div className="lg:col-span-4 text-[10px] text-slate-500">
            *Informações institucionais. Sujeito a alterações sem aviso prévio.
          </div>
        </section>

        <section id="canais" className="lb-band mt-5">
          <div className="max-w-6xl mx-auto px-6 py-5 grid grid-cols-1 lg:grid-cols-3 gap-3">
            <div className="lb-surface lb-block lb-block-flat p-4 text-slate-900">
              <div className="text-[11px] text-slate-600 font-semibold">Canais digitais</div>
              <h3 className="mt-2 text-lg font-semibold text-brand-ink font-sans">Acesso multicanal integrado</h3>
              <p className="text-sm text-slate-600 mt-2">Apps, banco pela internet e atendimento integrado.</p>
            </div>
            {[
              { title: 'App iOS', desc: 'Controle de conta e cartões no iPhone.' },
              { title: 'App Android', desc: 'Todas as funções com notificações instantâneas.' },
              { title: 'Banco pela internet', desc: 'Fluxos corporativos com aprovação.' },
            ].map((item) => (
              <div key={item.title} className="lb-panel lb-block lb-block-flat p-4 text-slate-900">
                <div className="text-xs font-semibold text-brand-ink">{item.title}</div>
                <div className="text-[11px] text-slate-600 mt-2">{item.desc}</div>
                <div className="mt-3 flex items-center gap-3">
                  <div className="w-14 h-14 border border-slate-200 bg-white flex items-center justify-center text-[10px] text-slate-400">QR</div>
                  <button type="button" className="px-3 py-1.5 rounded-sm border border-slate-200 text-[11px] font-medium">Acessar</button>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section id="atendimento" className="max-w-6xl mx-auto px-6 mt-5 grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-5">
          <div className="lb-panel lb-block lb-block-flat p-4 text-slate-900">
            <div className="text-[11px] text-slate-600 font-semibold">Atendimento pré-login</div>
            <h3 className="mt-2 text-lg font-semibold text-brand-ink font-sans">Central de apoio ao cliente</h3>
            <div className="mt-3 space-y-2 text-sm text-slate-600">
              <div>Central de ajuda e chat com assistente virtual.</div>
              <div>Telefones: 3003-0000 | 0800-000-000</div>
              <div>Horário: 24h para suporte digital, 8h-20h para assuntos comerciais.</div>
              <div>SAC: 0800-000-111 | Ouvidoria: 0800-000-222</div>
              <div>Atendimento a PCD: 0800-000-333</div>
            </div>
          </div>
          <div className="lb-surface lb-block lb-block-flat p-4 text-slate-900">
            <div className="text-[11px] text-slate-600 font-semibold">Como usar</div>
            <h4 id="como-usar" className="mt-2 text-base font-semibold text-brand-ink font-sans">Fluxo de primeiro acesso</h4>
            <ol className="mt-3 space-y-2 text-sm text-slate-600">
              <li>1. Crie sua conta digital e valide seus documentos.</li>
              <li>2. Baixe o app ou acesse o banco pela internet.</li>
              <li>3. Configure limites, notificações e segurança.</li>
            </ol>
            <div className="mt-3 text-[11px] text-slate-500">*Documentos sujeitos a validação automática e análise antifraude.</div>
            <div className="mt-1 text-[10px] text-slate-500">Prazo de resposta pode variar conforme horário bancário.</div>
          </div>
        </section>

        <section id="educacao" className="max-w-6xl mx-auto px-6 mt-5 grid grid-cols-1 lg:grid-cols-3 gap-3">
          {[
            { title: 'Educação financeira', desc: 'Conteúdos práticos para cada momento da sua vida financeira.' },
            { title: 'Loja / Benefícios', desc: 'Cashback, descontos e parceiros estratégicos.' },
            { title: 'Institucional e regulatório', desc: 'LGPD, política de privacidade e transparência.' },
          ].map((item) => (
            <div key={item.title} className="lb-panel lb-block lb-block-flat p-4 text-slate-900">
              <div className="text-xs font-semibold text-brand-ink">{item.title}</div>
              <div className="text-[11px] text-slate-600 mt-2">{item.desc}</div>
              <button type="button" className="mt-3 px-3 py-1.5 rounded-sm border border-slate-200 text-[11px] font-medium">
                Acessar
              </button>
            </div>
          ))}
        </section>

        <section className="max-w-6xl mx-auto px-6 mt-5">
          <div className="lb-panel lb-block lb-block-flat p-4 text-slate-900">
            <div className="text-[11px] text-slate-600 font-semibold">Componentes transversais</div>
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="border border-slate-200 p-3">
                <div className="text-xs font-semibold text-brand-ink">Modal informativo</div>
                <p className="text-[11px] text-slate-600 mt-2">Avisos importantes e termos exibidos antes da confirmação.</p>
                <button type="button" className="mt-3 px-3 py-1.5 rounded-sm bg-brand-dark text-white text-[11px] font-semibold">Ver exemplo</button>
              </div>
              <div className="border border-slate-200 p-3">
                <div className="text-xs font-semibold text-brand-ink">Tooltip legal</div>
                <p className="text-[11px] text-slate-600 mt-2">Detalhes sobre taxas e limites aparecem no hover.</p>
                <span className="lb-tooltip">Taxa efetiva anual*</span>
              </div>
              <div className="border border-slate-200 p-3">
                <div className="text-xs font-semibold text-brand-ink">Estado de loading</div>
                <div className="mt-3 h-2 w-full bg-slate-100 overflow-hidden">
                  <div className="h-full w-2/3 bg-brand-dark/60" />
                </div>
                <div className="text-[11px] text-slate-500 mt-2">Validando dados cadastrais...</div>
              </div>
              <div className="border border-slate-200 p-3">
                <div className="text-xs font-semibold text-brand-ink">Feedback de ação</div>
                <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 rounded-sm bg-emerald-50 text-emerald-700 text-[11px] font-semibold">
                  Solicitação enviada com sucesso
                </div>
                <div className="text-[11px] text-slate-500 mt-2">*Microcopy regulatório exibido junto à ação.</div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="lb-footer">
        <div className="max-w-6xl mx-auto px-6 py-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div>
            <div className="text-sm font-semibold">Produtos PF</div>
            <ul className="mt-3 space-y-2 text-xs lb-linklist">
              <li><a href="#">Conta, cartões e Pix</a></li>
              <li><a href="#">Empréstimos e seguros</a></li>
              <li><a href="#">Investimentos e consórcios</a></li>
              <li><a href="#">Tarifas e pacotes</a></li>
              <li><a href="#">Tabela de tarifas</a></li>
              <li><a href="#">Contratos e aditivos</a></li>
            </ul>
          </div>
          <div>
            <div className="text-sm font-semibold">Produtos PJ</div>
            <ul className="mt-3 space-y-2 text-xs lb-linklist">
              <li><a href="#">Pagamentos e cobrança</a></li>
              <li><a href="#">Gestão de caixa</a></li>
              <li><a href="#">Crédito empresarial</a></li>
              <li><a href="#">Câmbio e comércio exterior</a></li>
              <li><a href="#">Convênios e arrecadação</a></li>
              <li><a href="#">Boletos e liquidações</a></li>
            </ul>
          </div>
          <div>
            <div className="text-sm font-semibold">Atendimento</div>
            <ul className="mt-3 space-y-2 text-xs lb-linklist">
              <li><a href="#">Central de ajuda</a></li>
              <li><a href="#">Chat e telefones</a></li>
              <li><a href="#">SAC e Ouvidoria</a></li>
              <li><a href="#">Acessibilidade e PCD</a></li>
              <li><a href="#">Canal de denúncias</a></li>
              <li><a href="#">Canal de ética</a></li>
            </ul>
          </div>
          <div>
            <div className="text-sm font-semibold">Institucional</div>
            <ul className="mt-3 space-y-2 text-xs lb-linklist">
              <li><a href="#">Trabalhe conosco</a></li>
              <li><a href="#">Política de privacidade</a></li>
              <li><a href="#">Termos de uso</a></li>
              <li><a href="#">LGPD e reguladores</a></li>
              <li><a href="#">Transparência</a></li>
              <li><a href="#">Idioma</a></li>
              <li><a href="#">Código de conduta</a></li>
              <li><a href="#">Relações com investidores</a></li>
            </ul>
          </div>
        </div>
        <div className="max-w-6xl mx-auto px-6 pb-10 text-[11px] text-white/55 space-y-2">
          <div>Ouvidoria: 0800-000-222 | SAC: 0800-000-111 | Atendimento 24h digital.</div>
          <div>Avisos legais e condições vigentes. Banco autorizado e regulado conforme normas aplicáveis.</div>
          <div>*Operações sujeitas a análise de crédito e política de risco. Consulte tarifas e contratos vigentes.</div>
          <div>Canal de denúncias disponível 24h. Protocolo obrigatório para tratativas formais.</div>
        </div>
      </footer>
    </div>
  );
}
