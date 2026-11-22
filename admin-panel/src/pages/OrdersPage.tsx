import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import { api, refreshSessionTokens } from '../lib/api'
import { useAuth } from '../auth/useAuth'

type OrderStatus = 'aguardando_pagamento' | 'recebido' | 'em_preparo' | 'saiu_para_entrega' | 'entregue' | 'cancelado'

type Order = {
  id: string
  user_id: string
  itens: { prato_id: string; nome: string; preco_unitario: number; quantidade: number; observacao: string | null }[]
  subtotal: number
  desconto: number
  taxa_entrega: number
  total: number
  endereco_entrega: { rua: string; numero: string; bairro: string; cep: string | null; complemento: string | null }
  forma_pagamento: 'pix' | 'cartao' | 'dinheiro'
  status: OrderStatus
  criado_em: string
  atualizado_em: string
}

type OrdersPageData = {
  pedidos: Order[]
  pagina: number
  limite: number
  total: number
  total_paginas: number
}

type OrderEvent = { evento: 'pedido_criado' | 'pedido_status_atualizado' | 'pong'; pedido?: Order }
type ConnectionStatus = 'connecting' | 'connected' | 'reconnecting' | 'forbidden' | 'error'

const statusLabels: Record<OrderStatus, string> = {
  aguardando_pagamento: 'Aguardando pagamento',
  recebido: 'Recebido',
  em_preparo: 'Em preparo',
  saiu_para_entrega: 'Saiu para entrega',
  entregue: 'Entregue',
  cancelado: 'Cancelado',
}

const statusStyles: Record<OrderStatus, string> = {
  aguardando_pagamento: 'bg-milho/20 text-cafe',
  recebido: 'bg-urucum/10 text-urucum-escuro',
  em_preparo: 'bg-milho/25 text-cafe',
  saiu_para_entrega: 'bg-cafe-suave/15 text-cafe',
  entregue: 'bg-urucum/10 text-urucum',
  cancelado: 'bg-cafe-suave/15 text-cafe-suave',
}

function availableTransitions(status: OrderStatus): OrderStatus[] {
  switch (status) {
    case 'aguardando_pagamento': return ['cancelado']
    case 'recebido': return ['em_preparo', 'cancelado']
    case 'em_preparo': return ['saiu_para_entrega']
    case 'saiu_para_entrega': return ['entregue']
    default: return []
  }
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
}

function getWebSocketUrl(accessToken: string) {
  const apiBaseUrl = new URL(api.defaults.baseURL ?? 'http://localhost:8000', window.location.origin)
  const websocketProtocol = apiBaseUrl.protocol === 'https:' ? 'wss:' : 'ws:'
  const websocketUrl = new URL(apiBaseUrl)

  websocketUrl.protocol = websocketProtocol
  websocketUrl.pathname = `${websocketUrl.pathname.replace(/\/$/, '')}/pedidos/realtime-orders`
  websocketUrl.search = ''
  websocketUrl.searchParams.set('token', accessToken)

  return websocketUrl.toString()
}

export function OrdersPage() {
  const { accessToken } = useAuth()
  const [page, setPage] = useState(1)
  const [reloadKey, setReloadKey] = useState(0)
  const [pageData, setPageData] = useState<OrdersPageData | null>(null)
  const [loading, setLoading] = useState(true)
  const [pageError, setPageError] = useState('')
  const [connection, setConnection] = useState<ConnectionStatus>('connecting')
  const [selectedStatus, setSelectedStatus] = useState<Record<string, OrderStatus>>({})
  const [updatingId, setUpdatingId] = useState<string | null>(null)
  const [actionError, setActionError] = useState('')
  const [notice, setNotice] = useState('')
  const knownOrderIds = useRef(new Set<string>())
  const isLoaded = pageData !== null

  function reloadOrders() {
    setLoading(true)
    setPageError('')
    setReloadKey((value) => value + 1)
  }

  function changePage(nextPage: number) {
    setLoading(true)
    setPageError('')
    setPage(nextPage)
  }

  useEffect(() => {
    const controller = new AbortController()

    api.get<OrdersPageData>(`/pedidos/admin?pagina=${page}&limite=20`, { signal: controller.signal })
      .then(({ data }) => {
        if (controller.signal.aborted) return
        setPageData(data)
        data.pedidos.forEach((order) => knownOrderIds.current.add(order.id))
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        if (axios.isAxiosError(error) && error.response?.status === 403) {
          setPageError('Esta conta não tem permissão de administrador para listar pedidos.')
        } else {
          setPageError('Não foi possível carregar os pedidos. Verifique a API e tente novamente.')
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })

    return () => controller.abort()
  }, [page, reloadKey])

  useEffect(() => {
    if (!accessToken || !isLoaded) return

    let disposed = false
    let socket: WebSocket | null = null
    let reconnectTimer = 0
    let heartbeatTimer = 0
    let retryCount = 0

    const connect = () => {
      if (disposed) return
      setConnection(retryCount === 0 ? 'connecting' : 'reconnecting')
      socket = new WebSocket(getWebSocketUrl(accessToken))

      socket.onopen = () => {
        retryCount = 0
        setConnection('connected')
        heartbeatTimer = window.setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) socket.send('ping')
        }, 25_000)
      }

      socket.onmessage = (message) => {
        let event: OrderEvent
        try {
          event = JSON.parse(message.data) as OrderEvent
        } catch {
          return
        }
        if (!event.pedido || (event.evento !== 'pedido_criado' && event.evento !== 'pedido_status_atualizado')) return

        const order = event.pedido
        const isNewOrder = event.evento === 'pedido_criado' && !knownOrderIds.current.has(order.id)
        knownOrderIds.current.add(order.id)
        setPageData((current) => {
          if (!current) return current
          const index = current.pedidos.findIndex((item) => item.id === order.id)
          if (index >= 0) {
            const pedidos = [...current.pedidos]
            pedidos[index] = order
            return { ...current, pedidos }
          }
          if (event.evento === 'pedido_status_atualizado') return current
          const pedidos = page === 1 ? [order, ...current.pedidos].slice(0, current.limite) : current.pedidos
          const total = current.total + (isNewOrder ? 1 : 0)
          return { ...current, pedidos, total, total_paginas: Math.max(1, Math.ceil(total / current.limite)) }
        })

        if (isNewOrder) {
          setNotice(`Novo pedido recebido: #${order.id.slice(0, 8)}`)
          window.setTimeout(() => setNotice(''), 6_000)
        }
      }

      socket.onclose = (event) => {
        window.clearInterval(heartbeatTimer)
        if (disposed) return
        if (event.code === 4403) {
          setConnection('forbidden')
          return
        }
        if (event.code === 4401) {
          setConnection('reconnecting')
          void refreshSessionTokens().catch(() => setConnection('error'))
          return
        }

        retryCount += 1
        setConnection('reconnecting')
        const delay = Math.min(1_000 * 2 ** Math.min(retryCount - 1, 4), 15_000)
        reconnectTimer = window.setTimeout(connect, delay)
      }
    }

    connect()
    return () => {
      disposed = true
      window.clearTimeout(reconnectTimer)
      window.clearInterval(heartbeatTimer)
      socket?.close(1000, 'Page closed')
    }
  }, [accessToken, isLoaded, page])

  async function updateStatus(order: Order) {
    const status = selectedStatus[order.id]
    if (!status || status === order.status) return
    setActionError('')
    setUpdatingId(order.id)
    try {
      const { data } = await api.patch<Order>(`/pedidos/${order.id}/status`, { status })
      setPageData((current) => current ? {
        ...current,
        pedidos: current.pedidos.map((item) => item.id === data.id ? data : item),
      } : current)
      setSelectedStatus((current) => ({ ...current, [order.id]: data.status }))
    } catch (error: unknown) {
      if (axios.isAxiosError(error) && error.response?.status === 409) {
        setActionError(`A transição de ${statusLabels[order.status]} para ${statusLabels[status]} não é permitida.`)
      } else {
        setActionError(`Não foi possível atualizar o pedido #${order.id.slice(0, 8)}.`)
      }
    } finally {
      setUpdatingId(null)
    }
  }

  const connectionLabel: Record<ConnectionStatus, string> = {
    connecting: 'Conectando ao tempo real',
    connected: 'Tempo real conectado',
    reconnecting: 'Reconectando...',
    forbidden: 'Sem permissão para tempo real',
    error: 'Sessão expirada',
  }
  const connectionColor: Record<ConnectionStatus, string> = {
    connecting: 'bg-milho/20 text-cafe',
    connected: 'bg-milho/20 text-cafe',
    reconnecting: 'bg-milho/20 text-cafe',
    forbidden: 'bg-urucum/10 text-urucum-escuro',
    error: 'bg-urucum/10 text-urucum-escuro',
  }

  return (
    <div>
      <div className="mb-7 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="mb-2 text-xs font-bold tracking-[0.2em] text-urucum">OPERACAO</p>
          <h1 className="mb-2 text-3xl font-bold tracking-tight text-cafe">Pedidos</h1>
          <p className="text-sm text-cafe-suave">Acompanhe e atualize os pedidos em tempo real.</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`flex items-center gap-2 rounded-full px-3 py-2 text-xs font-semibold ${connectionColor[connection]}`}>
            <span className={`size-2 rounded-full ${connection === 'connected' ? 'bg-urucum' : connection === 'forbidden' || connection === 'error' ? 'bg-urucum-escuro' : 'bg-milho'}`} />
            {connectionLabel[connection]}
          </span>
          <button className="rounded-lg border border-cafe-suave/20 bg-white px-3 py-2 text-sm font-medium text-cafe transition hover:bg-tapioca disabled:opacity-50" disabled={loading} onClick={reloadOrders} type="button">Atualizar</button>
        </div>
      </div>

      {notice && <div className="mb-4 rounded-xl border border-milho/40 bg-milho/15 px-4 py-3 text-sm font-semibold text-cafe" role="status">{notice}</div>}
      {pageError && <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-urucum/20 bg-urucum/5 px-4 py-3 text-sm text-urucum-escuro" role="alert"><span>{pageError}</span><button className="font-semibold underline" onClick={reloadOrders} type="button">Tentar novamente</button></div>}
      {actionError && <div className="mb-4 rounded-xl border border-urucum/20 bg-urucum/5 px-4 py-3 text-sm text-urucum-escuro" role="alert">{actionError}</div>}

      <div className="mb-4 flex items-center justify-between text-sm text-cafe-suave">
        <span>{pageData ? `${pageData.total} pedido${pageData.total === 1 ? '' : 's'}` : 'Carregando pedidos...'}</span>
        <span>Página {pageData?.pagina ?? page} de {Math.max(pageData?.total_paginas ?? 1, 1)}</span>
      </div>

      {loading && !pageData && <div className="rounded-2xl border border-cafe-suave/15 bg-white p-10 text-center text-sm text-cafe-suave">Carregando pedidos...</div>}
      {!loading && !pageError && pageData?.pedidos.length === 0 && <div className="rounded-2xl border border-cafe-suave/15 bg-white p-12 text-center"><p className="mb-2 text-lg font-semibold text-cafe">Nenhum pedido por enquanto</p><p className="text-sm text-cafe-suave">Os novos pedidos aparecerão aqui automaticamente.</p></div>}

      <div className="grid gap-4">
        {pageData?.pedidos.map((order) => {
          const transitions = availableTransitions(order.status)
          const nextStatus = selectedStatus[order.id] ?? order.status
          const address = order.endereco_entrega
          return (
            <article className="rounded-2xl border border-cafe-suave/15 bg-white p-5 shadow-sm sm:p-6" key={order.id}>
              <div className="flex flex-wrap items-start justify-between gap-3 border-b border-cafe-suave/10 pb-4">
                <div>
                  <p className="mb-1 text-xs font-medium text-cafe-suave">Pedido <span className="font-mono text-cafe">#{order.id.slice(0, 8)}</span></p>
                  <p className="text-xs text-cafe-suave">{formatDate(order.criado_em)} · Cliente {order.user_id.slice(0, 8)}</p>
                </div>
                <span className={`rounded-full px-3 py-1.5 text-xs font-semibold ${statusStyles[order.status]}`}>{statusLabels[order.status]}</span>
              </div>

              <div className="grid gap-5 py-4 md:grid-cols-[1.4fr_1fr]">
                <div>
                  <h2 className="mb-2 text-xs font-bold uppercase tracking-wider text-cafe-suave">Itens</h2>
                  <ul className="grid gap-1.5">
                    {order.itens.map((item) => <li className="flex justify-between gap-3 text-sm text-cafe" key={`${order.id}-${item.prato_id}`}><span>{item.quantidade}x {item.nome}</span><span className="whitespace-nowrap text-cafe-suave">{formatCurrency(item.preco_unitario * item.quantidade)}</span></li>)}
                  </ul>
                </div>
                <div>
                  <h2 className="mb-2 text-xs font-bold uppercase tracking-wider text-cafe-suave">Entrega</h2>
                  <p className="text-sm text-cafe">{address.rua}, {address.numero}{address.complemento ? ` · ${address.complemento}` : ''}</p>
                  <p className="text-sm text-cafe-suave">{address.bairro}{address.cep ? ` · CEP ${address.cep}` : ''}</p>
                  <p className="mt-1 text-xs text-cafe-suave">Pagamento: {order.forma_pagamento}</p>
                </div>
              </div>

              <div className="flex flex-wrap items-end justify-between gap-4 border-t border-cafe-suave/10 pt-4">
                <div className="text-xs text-cafe-suave">Subtotal {formatCurrency(order.subtotal)}{order.desconto > 0 ? ` · Desconto ${formatCurrency(order.desconto)}` : ''} · Entrega {formatCurrency(order.taxa_entrega)}<p className="mt-1 text-lg font-bold text-cafe">Total {formatCurrency(order.total)}</p></div>
                {transitions.length > 0 && (
                  <div className="flex flex-wrap items-center gap-2">
                    <select aria-label={`Novo status do pedido ${order.id}`} className="rounded-lg border border-cafe-suave/20 bg-tapioca px-3 py-2 text-sm text-cafe outline-none focus:border-urucum" onChange={(event) => setSelectedStatus((current) => ({ ...current, [order.id]: event.target.value as OrderStatus }))} value={nextStatus}>
                      <option value={order.status}>{statusLabels[order.status]}</option>
                      {transitions.map((status) => <option key={status} value={status}>{statusLabels[status]}</option>)}
                    </select>
                    <button className="rounded-lg bg-urucum px-4 py-2 text-sm font-semibold text-white transition hover:bg-urucum-escuro disabled:cursor-not-allowed disabled:opacity-50" disabled={updatingId === order.id || nextStatus === order.status} onClick={() => { void updateStatus(order) }} type="button">{updatingId === order.id ? 'Salvando...' : 'Atualizar status'}</button>
                  </div>
                )}
              </div>
            </article>
          )
        })}
      </div>

      {pageData && pageData.total_paginas > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <button className="rounded-lg border border-cafe-suave/20 bg-white px-4 py-2 text-sm font-medium text-cafe transition hover:bg-tapioca disabled:cursor-not-allowed disabled:opacity-40" disabled={page <= 1 || loading} onClick={() => changePage(page - 1)} type="button">Anterior</button>
          <span className="text-sm text-cafe-suave">{pageData.pagina} / {pageData.total_paginas}</span>
          <button className="rounded-lg border border-cafe-suave/20 bg-white px-4 py-2 text-sm font-medium text-cafe transition hover:bg-tapioca disabled:cursor-not-allowed disabled:opacity-40" disabled={page >= pageData.total_paginas || loading} onClick={() => changePage(page + 1)} type="button">Próxima</button>
        </div>
      )}
    </div>
  )
}
