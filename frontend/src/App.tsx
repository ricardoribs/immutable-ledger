import { BrowserRouter, Routes, Route, Navigate, NavLink, Outlet, Link, useNavigate } from 'react-router-dom';
import { Bell } from 'lucide-react';
import { useAuthStore } from './store/authStore';
import Home from './pages/Home';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import PixPage from './pages/PixPage';
import Payments from './pages/Payments';
import Cards from './pages/Cards';
import Loans from './pages/Loans';
import Investments from './pages/Investments';
import Insurance from './pages/Insurance';
import Billing from './pages/Billing';
import PJ from './pages/PJ';
import OpenBanking from './pages/OpenBanking';
import Support from './pages/Support';
import Settings from './pages/Settings';
import Security from './pages/Security';
import Utilities from './pages/Utilities';
import Compliance from './pages/Compliance';
import Fraud from './pages/Fraud';
import Regulatory from './pages/Regulatory';
import Observability from './pages/Observability';
import Notifications from './pages/Notifications';
import Analytics from './pages/Analytics';
import FeatureFlags from './pages/FeatureFlags';

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function AppLayout() {
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `lb-navlink ${isActive ? 'lb-navlink-active' : ''}`;

  return (
    <div className="min-h-screen lb-app-shell text-slate-900">
      <header className="lb-app-header text-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/10 border border-white/20 flex items-center justify-center font-bold">
              LB
            </div>
            <div>
              <div className="text-base font-semibold">LuisBank</div>
              <div className="text-[11px] text-white/70">Institucional</div>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-3">
            <input className="lb-input" placeholder="Buscar serviços e operações" />
            <button className="relative w-10 h-10 rounded-sm border border-white/20 flex items-center justify-center text-white/80 hover:text-white">
              <Bell className="w-4 h-4" />
              <span className="absolute top-2.5 right-2.5 lb-notif-dot" />
            </button>
            <Link to="/app/support" className="px-3 py-2 rounded-sm bg-white text-brand-dark text-sm font-semibold">Central de ajuda</Link>
            <button
              onClick={() => { logout(); window.location.href = '/login'; }}
              className="px-3 py-2 rounded-sm border border-white/50 text-sm hover:bg-white/10"
            >
              Sair
            </button>
            <div className="lb-avatar">LR</div>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-6 mt-4 pb-12">
        <div className="grid grid-cols-1 lg:grid-cols-[230px_1fr] gap-6">
          <aside className="lb-card lb-card-info p-4">
            <div className="lb-nav-group">
              <div className="lb-nav-title">Conta</div>
              <nav className="space-y-1">
                <NavLink to="/app/dashboard" className={navLinkClass}>Visão geral</NavLink>
                <NavLink to="/app/settings" className={navLinkClass}>Configurações</NavLink>
                <NavLink to="/app/notifications" className={navLinkClass}>Notificações</NavLink>
              </nav>
            </div>
            <div className="lb-nav-group">
              <div className="lb-nav-title">Pagamentos</div>
              <nav className="space-y-1">
                <NavLink to="/app/pix" className={navLinkClass}>Pix</NavLink>
                <NavLink to="/app/payments" className={navLinkClass}>Pagamentos</NavLink>
                <NavLink to="/app/billing" className={navLinkClass}>Cobrança</NavLink>
              </nav>
            </div>
            <div className="lb-nav-group">
              <div className="lb-nav-title">Crédito</div>
              <nav className="space-y-1">
                <NavLink to="/app/cards" className={navLinkClass}>Cartões</NavLink>
                <NavLink to="/app/loans" className={navLinkClass}>Empréstimos</NavLink>
              </nav>
            </div>
            <div className="lb-nav-group">
              <div className="lb-nav-title">Investimentos</div>
              <nav className="space-y-1">
                <NavLink to="/app/investments" className={navLinkClass}>Investimentos</NavLink>
                <NavLink to="/app/insurance" className={navLinkClass}>Seguros</NavLink>
                <NavLink to="/app/pj" className={navLinkClass}>PJ</NavLink>
                <NavLink to="/app/open-banking" className={navLinkClass}>Open Finance</NavLink>
              </nav>
            </div>
            <div className="lb-nav-group">
              <div className="lb-nav-title">Compliance & Segurança</div>
              <nav className="space-y-1">
                <NavLink to="/app/security" className={navLinkClass}>Segurança</NavLink>
                <NavLink to="/app/compliance" className={navLinkClass}>LGPD</NavLink>
                <NavLink to="/app/fraud" className={navLinkClass}>Fraude</NavLink>
                <NavLink to="/app/regulatory" className={navLinkClass}>Regulatório</NavLink>
              </nav>
            </div>
            <div className="lb-nav-group">
              <div className="lb-nav-title">Operações</div>
              <nav className="space-y-1">
                <NavLink to="/app/support" className={navLinkClass}>Atendimento</NavLink>
                <NavLink to="/app/utilities" className={navLinkClass}>Serviços</NavLink>
                <NavLink to="/app/observability" className={navLinkClass}>Observabilidade</NavLink>
                <NavLink to="/app/analytics" className={navLinkClass}>Análises e ML</NavLink>
                <NavLink to="/app/feature-flags" className={navLinkClass}>Flags de funcionalidades</NavLink>
              </nav>
            </div>
          </aside>
          <main className="space-y-5">
            <div className="lb-card lb-card-util lb-card-compact flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="lb-label">Visão geral</div>
                <div className="text-base font-semibold text-slate-900">Painel operacional</div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => navigate('/app/payments')} className="px-3 py-2 rounded-sm bg-slate-900 text-white text-xs">Nova transferência</button>
                <button onClick={() => navigate('/app/analytics')} className="px-3 py-2 rounded-sm border border-slate-300 text-xs">Relatórios</button>
              </div>
            </div>
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="pix" element={<PixPage />} />
          <Route path="payments" element={<Payments />} />
          <Route path="cards" element={<Cards />} />
          <Route path="loans" element={<Loans />} />
          <Route path="investments" element={<Investments />} />
          <Route path="insurance" element={<Insurance />} />
          <Route path="billing" element={<Billing />} />
          <Route path="pj" element={<PJ />} />
          <Route path="open-banking" element={<OpenBanking />} />
          <Route path="support" element={<Support />} />
          <Route path="security" element={<Security />} />
          <Route path="compliance" element={<Compliance />} />
          <Route path="fraud" element={<Fraud />} />
          <Route path="regulatory" element={<Regulatory />} />
          <Route path="observability" element={<Observability />} />
          <Route path="notifications" element={<Notifications />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="feature-flags" element={<FeatureFlags />} />
          <Route path="utilities" element={<Utilities />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
