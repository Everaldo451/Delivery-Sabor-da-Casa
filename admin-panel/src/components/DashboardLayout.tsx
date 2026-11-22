import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

export function DashboardLayout() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    try {
      await logout()
    } finally {
      navigate('/login', { replace: true })
    }
  }

  return (
    <div className="min-h-screen bg-tapioca">
      <aside className="fixed inset-y-0 left-0 z-20 flex w-64 flex-col border-r border-cafe-suave/15 bg-white px-4 py-6 max-[760px]:w-[76px] max-[760px]:px-2">
        <div className="mb-10 flex items-center gap-3 px-2 max-[760px]:justify-center max-[760px]:px-0">
          <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-urucum text-sm font-extrabold tracking-tight text-white">SC</span>
          <div className="flex flex-col max-[760px]:hidden"><strong className="text-sm font-bold text-cafe">Sabor da Casa</strong><span className="text-xs text-cafe-suave">Painel administrativo</span></div>
        </div>
        <p className="mb-2 px-3 text-[10px] font-bold tracking-[0.2em] text-cafe-suave/70 max-[760px]:hidden">MENU</p>
        <nav aria-label="Navegação principal" className="grid gap-1">
          <NavLink className={({ isActive }) => `flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm transition max-[760px]:flex-col max-[760px]:justify-center max-[760px]:gap-0 max-[760px]:px-1 max-[760px]:py-2 max-[760px]:text-[10px] ${isActive ? 'bg-urucum/10 font-semibold text-urucum-escuro' : 'text-cafe-suave hover:bg-tapioca hover:text-cafe'}`} end to="/"><span aria-hidden="true" className="w-5 text-center text-lg">⌂</span><span className="max-[760px]:text-center">In&iacute;cio</span></NavLink>
          <NavLink className={({ isActive }) => `flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm transition max-[760px]:flex-col max-[760px]:justify-center max-[760px]:gap-0 max-[760px]:px-1 max-[760px]:py-2 max-[760px]:text-[10px] ${isActive ? 'bg-urucum/10 font-semibold text-urucum-escuro' : 'text-cafe-suave hover:bg-tapioca hover:text-cafe'}`} to="/pedidos"><span aria-hidden="true" className="w-5 text-center text-lg">▤</span><span className="max-[760px]:text-center">Pedidos</span></NavLink>
          <NavLink className={({ isActive }) => `flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm transition max-[760px]:flex-col max-[760px]:justify-center max-[760px]:gap-0 max-[760px]:px-1 max-[760px]:py-2 max-[760px]:text-[10px] ${isActive ? 'bg-urucum/10 font-semibold text-urucum-escuro' : 'text-cafe-suave hover:bg-tapioca hover:text-cafe'}`} to="/cardapio"><span aria-hidden="true" className="w-5 text-center text-lg">▦</span><span className="max-[760px]:text-center">Card&aacute;pio</span></NavLink>
        </nav>
        <button className="mt-auto flex min-h-12 items-center gap-3 border-t border-cafe-suave/15 px-3 pt-3 text-left text-sm text-cafe-suave transition hover:text-urucum-escuro max-[760px]:flex-col max-[760px]:justify-center max-[760px]:gap-0 max-[760px]:px-0 max-[760px]:text-[10px]" onClick={() => { void handleLogout().catch(() => undefined) }} type="button">
          <span aria-hidden="true" className="w-5 text-center text-lg">↪</span>Sair
        </button>
      </aside>
      <div className="ml-64 min-h-screen max-[760px]:ml-[76px]">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-cafe-suave/15 bg-white/90 px-10 text-sm text-cafe backdrop-blur max-[760px]:h-14 max-[760px]:px-4">
          <span className="font-medium">Administra&ccedil;&atilde;o</span><span className="flex items-center gap-2 text-xs text-cafe-suave"><span className="size-2 rounded-full bg-milho" />Sess&atilde;o ativa</span>
        </header>
        <main className="mx-auto w-full max-w-6xl px-10 py-10 max-[760px]:px-4 max-[760px]:py-6"><Outlet /></main>
      </div>
    </div>
  )
}
