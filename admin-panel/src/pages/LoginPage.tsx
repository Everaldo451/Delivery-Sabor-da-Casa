import { useState, type FormEvent } from 'react'
import { useAuth } from '../auth/useAuth'

export function LoginPage() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, senha)
    } catch {
      setError('Falha no login. Verifique seu email e sua senha.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-[radial-gradient(ellipse_at_top_left,_#F2A93B33_0%,_#FBF7F2_58%,_#FBF7F2_100%)] px-4 py-10">
      <form className="w-full max-w-md rounded-3xl border border-white/90 bg-white p-7 shadow-[0_28px_80px_rgba(43,29,23,0.14)] sm:p-10" onSubmit={handleSubmit}>
        <div className="mx-auto mb-5 grid size-14 place-items-center rounded-2xl bg-urucum text-lg font-extrabold tracking-tight text-white shadow-lg shadow-urucum/20">SC</div>
        <p className="mb-2 text-center text-xs font-bold tracking-[0.22em] text-urucum">SABOR DA CASA</p>
        <h1 className="mb-2 text-center text-3xl font-bold tracking-tight text-cafe">Entrar no painel</h1>
        <p className="mb-8 text-center text-sm leading-6 text-cafe-suave">Use sua conta de administrador para continuar.</p>

        <label className="mb-2 block text-sm font-semibold text-cafe" htmlFor="email">E-mail</label>
        <input
          className="mb-5 block w-full rounded-xl border border-cafe-suave/25 bg-tapioca px-4 py-3 text-cafe outline-none transition placeholder:text-cafe-suave/60 focus:border-urucum focus:bg-white focus:ring-4 focus:ring-urucum/10"
          autoComplete="username"
          id="email"
          name="email"
          onChange={(event) => setEmail(event.target.value)}
          required
          type="email"
          value={email}
        />

        <label className="mb-2 block text-sm font-semibold text-cafe" htmlFor="senha">Senha</label>
        <input
          className="block w-full rounded-xl border border-cafe-suave/25 bg-tapioca px-4 py-3 text-cafe outline-none transition placeholder:text-cafe-suave/60 focus:border-urucum focus:bg-white focus:ring-4 focus:ring-urucum/10"
          autoComplete="current-password"
          id="senha"
          name="senha"
          onChange={(event) => setSenha(event.target.value)}
          required
          type="password"
          value={senha}
        />

        {error && <p className="mt-4 rounded-xl border border-urucum/20 bg-urucum/5 px-4 py-3 text-sm text-urucum-escuro" role="alert">{error}</p>}
        <button className="mt-7 w-full rounded-xl bg-urucum px-4 py-3.5 font-semibold text-white shadow-lg shadow-urucum/15 transition hover:bg-urucum-escuro focus:outline-none focus:ring-4 focus:ring-urucum/20 disabled:cursor-wait disabled:opacity-60" disabled={loading} type="submit">
          {loading ? 'Entrando...' : 'Entrar'}
        </button>
        <p className="mt-6 text-center text-xs text-cafe-suave">Acesso restrito à equipe administrativa</p>
      </form>
    </main>
  )
}
