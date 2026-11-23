import { useEffect, useMemo, useState, type FormEvent } from 'react'
import axios from 'axios'
import { api } from '../lib/api'

type Category = { id: number; nome: string }
type Dish = { id: string; nome: string; descricao: string; preco: number | string; categoria: string; imagem: { url: string; content_type: string } | null; disponivel: boolean }
type DishForm = { nome: string; descricao: string; preco: string; categoria: string; disponivel: boolean }
const emptyForm: DishForm = { nome: '', descricao: '', preco: '', categoria: '', disponivel: true }

function errorMessage(error: unknown, fallback: string) {
  return axios.isAxiosError<{ detail?: string }>(error) && typeof error.response?.data?.detail === 'string' ? error.response.data.detail : fallback
}

function imageUrl(path: string) {
  const base = api.defaults.baseURL ?? window.location.origin
  return new URL(path, `${base.replace(/\/$/, '')}/`).toString()
}

export function MenuPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [dishes, setDishes] = useState<Dish[]>([])
  const [categoryFilter, setCategoryFilter] = useState('')
  const [categoryName, setCategoryName] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [reload, setReload] = useState(0)
  const [pageError, setPageError] = useState('')
  const [categoryError, setCategoryError] = useState('')
  const [formError, setFormError] = useState('')
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Dish | null>(null)
  const [form, setForm] = useState<DishForm>(emptyForm)
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [deletingDish, setDeletingDish] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    Promise.all([api.get<Category[]>('/cardapio/categorias'), api.get<Dish[]>('/cardapio')])
      .then(([categoryResponse, dishResponse]) => {
        if (!active) return
        setCategories(categoryResponse.data)
        setDishes(dishResponse.data)
        setPageError('')
      })
      .catch((error: unknown) => { if (active) setPageError(errorMessage(error, 'Não foi possível carregar o cardápio.')) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [reload])

  const visibleDishes = useMemo(() => categoryFilter ? dishes.filter((dish) => dish.categoria === categoryFilter) : dishes, [categoryFilter, dishes])
  const refresh = () => { setLoading(true); setReload((version) => version + 1) }

  function openNew() {
    setEditing(null)
    setForm({ ...emptyForm, categoria: categories[0]?.nome ?? '' })
    setImageFile(null)
    setFormError('')
    setDialogOpen(true)
  }

  function openEdit(dish: Dish) {
    setEditing(dish)
    setForm({ nome: dish.nome, descricao: dish.descricao, preco: String(dish.preco), categoria: dish.categoria, disponivel: dish.disponivel })
    setImageFile(null)
    setFormError('')
    setDialogOpen(true)
  }

  async function saveCategory(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setCategoryError('')
    setSaving(true)
    try { await api.post('/cardapio/categorias', { nome: categoryName }); setCategoryName(''); refresh() }
    catch (error: unknown) { setCategoryError(errorMessage(error, 'Não foi possível criar a categoria.')) }
    finally { setSaving(false) }
  }

  async function removeCategory(category: Category) {
    setCategoryError('')
    try {
      await api.delete(`/cardapio/categorias/${category.id}`)
      if (categoryFilter === category.nome) setCategoryFilter('')
      refresh()
    } catch (error: unknown) { setCategoryError(errorMessage(error, `Não foi possível remover ${category.nome}.`)) }
  }

  async function saveDish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError('')
    setSaving(true)
    try {
      const payload = { ...form, preco: Number(form.preco) }
      const response = editing
        ? await api.put<Dish>(`/cardapio/${editing.id}`, payload)
        : await api.post<Dish>('/cardapio', payload)
      if (imageFile) await api.put(`/cardapio/${response.data.id}/imagem`, imageFile, { headers: { 'Content-Type': imageFile.type } })
      setDialogOpen(false)
      refresh()
    } catch (error: unknown) { setFormError(errorMessage(error, 'Não foi possível salvar o prato.')) }
    finally { setSaving(false) }
  }

  async function removeDish(dish: Dish) {
    setDeletingDish(dish.id)
    setPageError('')
    try { await api.delete(`/cardapio/${dish.id}`); refresh() }
    catch (error: unknown) { setPageError(errorMessage(error, `Não foi possível remover ${dish.nome}.`)) }
    finally { setDeletingDish(null) }
  }

  return <div>
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div><p className="mb-2 text-xs font-bold tracking-[0.2em] text-urucum">CATÁLOGO</p><h1 className="mb-2 text-3xl font-bold tracking-tight text-cafe">Cardápio</h1><p className="text-sm text-cafe-suave">Gerencie pratos, categorias, preços e disponibilidade.</p></div>
      <button className="rounded-xl bg-urucum px-5 py-3 text-sm font-semibold text-white transition hover:bg-urucum-escuro disabled:opacity-50" disabled={!categories.length} onClick={openNew} type="button">+ Novo prato</button>
    </div>
    {pageError && <div className="mb-5 rounded-xl border border-urucum/20 bg-urucum/5 px-4 py-3 text-sm text-urucum-escuro" role="alert">{pageError}</div>}
    <section className="mb-7 rounded-2xl border border-cafe-suave/15 bg-white p-5 shadow-sm sm:p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3"><div><h2 className="mb-1 text-base font-bold text-cafe">Categorias</h2><p className="text-xs text-cafe-suave">Filtre o cardápio ou cadastre uma categoria.</p></div>
        <form className="flex gap-2" onSubmit={(event) => { void saveCategory(event) }}><input aria-label="Nome da nova categoria" className="w-44 rounded-lg border border-cafe-suave/20 bg-tapioca px-3 py-2 text-sm text-cafe outline-none focus:border-urucum sm:w-56" maxLength={80} onChange={(event) => setCategoryName(event.target.value)} placeholder="Nova categoria" required value={categoryName} /><button className="rounded-lg border border-cafe-suave/20 px-3 py-2 text-sm font-semibold text-cafe hover:bg-tapioca disabled:opacity-50" disabled={saving} type="submit">Adicionar</button></form>
      </div>
      {categoryError && <p className="mb-3 text-sm text-urucum-escuro" role="alert">{categoryError}</p>}
      <div className="flex flex-wrap gap-2"><button className={`rounded-full px-4 py-2 text-xs font-semibold ${categoryFilter === '' ? 'bg-cafe text-white' : 'bg-tapioca text-cafe-suave hover:bg-milho/20'}`} onClick={() => setCategoryFilter('')} type="button">Todos ({dishes.length})</button>
        {categories.map((category) => { const count = dishes.filter((dish) => dish.categoria === category.nome).length; return <div className="flex items-center overflow-hidden rounded-full border border-cafe-suave/15" key={category.id}><button className={`px-3 py-2 text-xs font-semibold ${categoryFilter === category.nome ? 'bg-urucum text-white' : 'bg-white text-cafe-suave hover:bg-tapioca'}`} onClick={() => setCategoryFilter(category.nome)} type="button">{category.nome} ({count})</button><button aria-label={`Remover categoria ${category.nome}`} className="self-stretch border-l border-cafe-suave/15 px-2 text-cafe-suave hover:bg-urucum/10 hover:text-urucum-escuro disabled:opacity-30" disabled={count > 0} onClick={() => { void removeCategory(category) }} title={count ? 'Remova primeiro os pratos desta categoria' : 'Remover categoria'} type="button">×</button></div> })}
      </div>
    </section>
    <div className="mb-3 flex items-center justify-between text-sm text-cafe-suave"><span>{loading ? 'Carregando cardápio...' : `${visibleDishes.length} prato${visibleDishes.length === 1 ? '' : 's'}`}</span><button className="rounded-lg px-3 py-2 text-xs font-semibold hover:bg-white hover:text-cafe" disabled={loading} onClick={refresh} type="button">Atualizar</button></div>
    {loading && dishes.length === 0 && <div className="rounded-2xl border border-cafe-suave/15 bg-white p-10 text-center text-sm text-cafe-suave">Carregando pratos e categorias...</div>}
    {!loading && visibleDishes.length === 0 && <div className="rounded-2xl border border-cafe-suave/15 bg-white p-12 text-center"><p className="mb-2 text-lg font-semibold text-cafe">Nenhum prato nesta categoria</p><p className="text-sm text-cafe-suave">Adicione um prato para começar.</p></div>}
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">{visibleDishes.map((dish) => <article className="overflow-hidden rounded-2xl border border-cafe-suave/15 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md" key={dish.id}>
      <div className="relative h-44 bg-tapioca">{dish.imagem ? <img alt={dish.nome} className="size-full object-cover" loading="lazy" src={imageUrl(dish.imagem.url)} /> : <div className="grid size-full place-items-center text-4xl text-milho">✦</div>}<span className={`absolute right-3 top-3 rounded-full px-3 py-1 text-[10px] font-bold ${dish.disponivel ? 'bg-white/95 text-urucum' : 'bg-cafe/90 text-white'}`}>{dish.disponivel ? 'Disponível' : 'Indisponível'}</span></div>
      <div className="p-5"><div className="mb-2 flex items-start justify-between gap-3"><div><p className="mb-1 text-[10px] font-bold uppercase tracking-[0.16em] text-urucum">{dish.categoria}</p><h2 className="mb-0 text-lg font-bold text-cafe">{dish.nome}</h2></div><span className="whitespace-nowrap text-sm font-bold text-cafe">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(dish.preco))}</span></div><p className="mb-5 line-clamp-2 min-h-10 text-sm leading-5 text-cafe-suave">{dish.descricao}</p><div className="flex gap-2 border-t border-cafe-suave/10 pt-3"><button className="flex-1 rounded-lg border border-cafe-suave/20 px-3 py-2 text-xs font-semibold text-cafe hover:bg-tapioca" onClick={() => openEdit(dish)} type="button">Editar</button><button className="rounded-lg px-3 py-2 text-xs font-semibold text-urucum-escuro hover:bg-urucum/5 disabled:opacity-50" disabled={deletingDish === dish.id} onClick={() => { void removeDish(dish) }} type="button">{deletingDish === dish.id ? 'Removendo...' : 'Remover'}</button></div></div>
    </article>)}</div>
    {dialogOpen && <div className="fixed inset-0 z-40 grid place-items-center overflow-y-auto bg-cafe/50 p-4" onMouseDown={(event) => { if (event.target === event.currentTarget) setDialogOpen(false) }}><section aria-labelledby="dish-dialog-title" aria-modal="true" className="my-8 w-full max-w-xl rounded-2xl bg-white p-6 shadow-2xl" role="dialog"><div className="mb-5 flex items-center justify-between"><h2 className="text-xl font-bold text-cafe" id="dish-dialog-title">{editing ? 'Editar prato' : 'Novo prato'}</h2><button aria-label="Fechar" className="rounded-lg px-3 py-1 text-xl text-cafe-suave hover:bg-tapioca" onClick={() => setDialogOpen(false)} type="button">×</button></div>
      {formError && <p className="mb-4 rounded-lg bg-urucum/5 p-3 text-sm text-urucum-escuro" role="alert">{formError}</p>}
      <form className="grid gap-4" onSubmit={(event) => { void saveDish(event) }}><label className="grid gap-1 text-sm font-medium text-cafe">Nome<input className="rounded-lg border border-cafe-suave/20 px-3 py-2 outline-none focus:border-urucum" maxLength={120} onChange={(event) => setForm({ ...form, nome: event.target.value })} required value={form.nome} /></label>
        <label className="grid gap-1 text-sm font-medium text-cafe">Descrição<textarea className="rounded-lg border border-cafe-suave/20 px-3 py-2 outline-none focus:border-urucum" onChange={(event) => setForm({ ...form, descricao: event.target.value })} required rows={3} value={form.descricao} /></label>
        <div className="grid gap-4 sm:grid-cols-2"><label className="grid gap-1 text-sm font-medium text-cafe">Preço (R$)<input className="rounded-lg border border-cafe-suave/20 px-3 py-2 outline-none focus:border-urucum" min="0.01" onChange={(event) => setForm({ ...form, preco: event.target.value })} required step="0.01" type="number" value={form.preco} /></label><label className="grid gap-1 text-sm font-medium text-cafe">Categoria<select className="rounded-lg border border-cafe-suave/20 bg-white px-3 py-2 outline-none focus:border-urucum" onChange={(event) => setForm({ ...form, categoria: event.target.value })} required value={form.categoria}>{categories.map((category) => <option key={category.id} value={category.nome}>{category.nome}</option>)}</select></label></div>
        <label className="grid gap-1 text-sm font-medium text-cafe">Imagem (JPEG, PNG ou WebP)<input accept="image/jpeg,image/png,image/webp" className="rounded-lg border border-cafe-suave/20 px-3 py-2 text-sm" onChange={(event) => setImageFile(event.target.files?.[0] ?? null)} type="file" /></label>
        <label className="flex items-center gap-2 text-sm text-cafe"><input checked={form.disponivel} onChange={(event) => setForm({ ...form, disponivel: event.target.checked })} type="checkbox" />Disponível para pedidos</label>
        <div className="mt-2 flex justify-end gap-2"><button className="rounded-lg px-4 py-2 text-sm text-cafe-suave hover:bg-tapioca" onClick={() => setDialogOpen(false)} type="button">Cancelar</button><button className="rounded-lg bg-urucum px-4 py-2 text-sm font-semibold text-white hover:bg-urucum-escuro disabled:opacity-50" disabled={saving} type="submit">{saving ? 'Salvando...' : 'Salvar prato'}</button></div>
      </form></section></div>}
  </div>
}
