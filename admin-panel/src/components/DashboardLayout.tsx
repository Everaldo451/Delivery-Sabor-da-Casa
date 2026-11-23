import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

export function DashboardLayout() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(
    () => localStorage.getItem('admin.sidebar.open') !== 'false',
  )

  useEffect(() => {
    localStorage.setItem('admin.sidebar.open', String(sidebarOpen))
  }, [sidebarOpen])

  async function handleLogout() {
    try {
      await logout()
    } finally {
      navigate('/login', { replace: true })
    }
  }

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex min-h-11 items-center rounded-xl text-sm transition-colors duration-200 ${sidebarOpen ? 'justify-start gap-3 px-3' : 'justify-center px-2'} ${isActive ? 'bg-urucum/10 font-semibold text-urucum-escuro' : 'text-cafe-suave hover:bg-tapioca hover:text-cafe'}`
  const labelClass = `overflow-hidden whitespace-nowrap transition-[max-width,opacity] duration-200 ${sidebarOpen ? 'max-w-40 opacity-100' : 'max-w-0 opacity-0'}`

  return (
    <div className="min-h-screen bg-tapioca">
      <aside className={`fixed inset-y-0 left-0 z-20 flex flex-col overflow-hidden border-r border-cafe-suave/15 bg-white py-6 transition-[width] duration-300 ease-in-out ${sidebarOpen ? 'w-64 px-4' : 'w-20 px-3'}`}>
        <div className={`mb-10 flex h-11 shrink-0 items-center ${sidebarOpen ? 'gap-3 px-2' : 'justify-center'}`}>
          <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-urucum text-sm font-extrabold tracking-tight text-white">SC</span>
          <div className={`flex flex-col overflow-hidden whitespace-nowrap transition-[max-width,opacity] duration-200 ${sidebarOpen ? 'max-w-40 opacity-100' : 'max-w-0 opacity-0'}`}>
            <strong className="text-sm font-bold text-cafe">Sabor da Casa</strong>
            <span className="text-xs text-cafe-suave">Painel administrativo</span>
          </div>
        </div>

        <p className={`mb-2 overflow-hidden px-3 text-[10px] font-bold tracking-[0.2em] text-cafe-suave/70 transition-opacity duration-150 ${sidebarOpen ? 'opacity-100' : 'opacity-0'}`}>MENU</p>
        <nav aria-label="Navegação principal" className="grid gap-1">
          <NavLink aria-label="Início" className={navLinkClass} end title={!sidebarOpen ? 'Início' : undefined} to="/">
            <span aria-hidden="true" className="w-5 shrink-0 text-center text-lg">⌂</span><span className={labelClass}>In&iacute;cio</span>
          </NavLink>
          <NavLink aria-label="Pedidos" className={navLinkClass} title={!sidebarOpen ? 'Pedidos' : undefined} to="/pedidos">
            <span aria-hidden="true" className="w-5 shrink-0 text-center text-lg">▤</span><span className={labelClass}>Pedidos</span>
          </NavLink>
          <NavLink aria-label="Cardápio" className={navLinkClass} title={!sidebarOpen ? 'Cardápio' : undefined} to="/cardapio">
            <span aria-hidden="true" className="w-5 shrink-0 text-center text-lg">▦</span><span className={labelClass}>Card&aacute;pio</span>
          </NavLink>
          <NavLink aria-label="Zonas de entrega" className={navLinkClass} title={!sidebarOpen ? 'Zonas de entrega' : undefined} to="/zonas-entrega">
            <span aria-hidden="true" className="w-5 shrink-0 text-center text-lg">⌖</span><span className={labelClass}>Zonas de entrega</span>
          </NavLink>
        </nav>

        <button className={`mt-auto flex min-h-12 items-center border-t border-cafe-suave/15 pt-3 text-sm text-cafe-suave transition hover:text-urucum-escuro ${sidebarOpen ? 'gap-3 px-3 text-left' : 'justify-center'}`} onClick={() => { void handleLogout().catch(() => undefined) }} type="button">
          <span aria-hidden="true" className="w-5 shrink-0 text-center text-lg">↪</span><span className={labelClass}>Sair</span>
        </button>
      </aside>

      <div className={`min-h-screen transition-[margin] duration-300 ease-in-out ${sidebarOpen ? 'ml-64' : 'ml-20'}`}>
        <header className="sticky top-0 z-10 flex h-16 items-center gap-4 border-b border-cafe-suave/15 bg-white/90 px-8 text-sm text-cafe backdrop-blur max-[760px]:h-14 max-[760px]:gap-3 max-[760px]:px-4">
          <button
            aria-expanded={sidebarOpen}
            aria-label={sidebarOpen ? 'Recolher menu lateral' : 'Expandir menu lateral'}
            className="grid size-9 shrink-0 place-items-center rounded-lg border border-cafe-suave/20 bg-white text-lg text-cafe transition hover:bg-tapioca focus:outline-none focus:ring-4 focus:ring-urucum/15"
            onClick={() => setSidebarOpen((open) => !open)}
            type="button"
          >
            <span aria-hidden="true" className={`transition-transform duration-300 ${sidebarOpen ? '' : 'rotate-180'}`}>‹</span>
          </button>
          <span className="font-medium">Administra&ccedil;&atilde;o</span>
          <span className="ml-auto flex items-center gap-2 text-xs text-cafe-suave"><span className="size-2 rounded-full bg-milho" />Sess&atilde;o ativa</span>
        </header>
        <main className="mx-auto w-full max-w-6xl px-10 py-10 max-[760px]:px-4 max-[760px]:py-6"><Outlet /></main>
      </div>
    </div>
  )
}
