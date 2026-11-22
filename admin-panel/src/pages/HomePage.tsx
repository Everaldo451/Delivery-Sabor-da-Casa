export function HomePage() {
  return (
    <>
      <div className="mb-8"><p className="mb-2 text-xs font-bold tracking-[0.2em] text-urucum">PAINEL</p><h1 className="mb-2 text-3xl font-bold tracking-tight text-cafe">Vis&atilde;o geral</h1><p className="text-sm leading-6 text-cafe-suave">Bem-vindo ao painel administrativo do Sabor da Casa.</p></div>
      <section className="flex min-h-52 items-center justify-between rounded-2xl border border-milho/30 bg-gradient-to-br from-white to-milho/10 p-8 shadow-sm max-[760px]:gap-4 max-[760px]:p-5">
        <div><p className="mb-2 text-xs font-bold tracking-[0.2em] text-urucum">TUDO PRONTO</p><h2 className="mb-2 text-xl font-bold text-cafe">Seu painel est&aacute; conectado</h2><p className="text-sm leading-6 text-cafe-suave">Use o menu lateral para acessar pedidos e gerenciar o card&aacute;pio.</p></div>
        <span className="grid size-16 shrink-0 place-items-center rounded-2xl bg-milho/20 text-3xl text-urucum max-[760px]:size-12" aria-hidden="true">✦</span>
      </section>
    </>
  )
}
