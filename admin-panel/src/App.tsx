import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/useAuth'
import { DashboardLayout } from './components/DashboardLayout'
import { LoginPage } from './pages/LoginPage'
import { HomePage } from './pages/HomePage'
import { OrdersPage } from './pages/OrdersPage'
import { MenuPage } from './pages/MenuPage'
import { DeliveryZonesPage } from './pages/DeliveryZonesPage'

function ProtectedLayout() {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <DashboardLayout /> : <Navigate to="/login" replace />
}

function LoginRoute() {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
}

function NotFoundPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-tapioca p-6">
      <section className="w-full max-w-lg rounded-2xl border border-cafe-suave/15 bg-white p-8 text-center shadow-sm">
        <p className="mb-2 text-sm font-semibold uppercase tracking-[0.18em] text-urucum">Erro 404</p>
        <h1 className="mb-2 text-2xl font-bold text-cafe">Página não encontrada</h1>
        <p className="text-cafe-suave">Confira o endereço e tente novamente.</p>
      </section>
    </main>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginRoute />} />
      <Route element={<ProtectedLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/pedidos" element={<OrdersPage />} />
        <Route path="/cardapio" element={<MenuPage />} />
        <Route path="/zonas-entrega" element={<DeliveryZonesPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
