import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import L from 'leaflet'
import { MapContainer, TileLayer, useMap } from 'react-leaflet'
import type { FeatureCollection, Geometry } from 'geojson'
import 'leaflet/dist/leaflet.css'
import { api } from '../lib/api'

type ZoneProperties = { nome: string; valor: number }
type ZoneCollection = FeatureCollection<Geometry, ZoneProperties>

function errorMessage(error: unknown, fallback: string) {
  return axios.isAxiosError<{ detail?: string }>(error) && typeof error.response?.data?.detail === 'string' ? error.response.data.detail : fallback
}

function ZoneLayers({ zones }: { zones: ZoneCollection }) {
  const map = useMap()
  const layer = useMemo(() => L.geoJSON(zones, {
    style: () => ({ color: '#B93A1E', weight: 2, fillColor: '#F2A93B', fillOpacity: 0.3 }),
    onEachFeature: (feature, featureLayer) => {
      const properties = feature.properties as ZoneProperties
      const tooltip = document.createElement('div')
      tooltip.textContent = `${properties.nome} · ${new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(properties.valor)}`
      featureLayer.bindTooltip(tooltip, { sticky: true })
      featureLayer.on({
        mouseover: () => { if (featureLayer instanceof L.Path) featureLayer.setStyle({ color: '#BF2A14', weight: 3, fillOpacity: 0.55 }) },
        mouseout: () => { if (featureLayer instanceof L.Path) featureLayer.setStyle({ color: '#B93A1E', weight: 2, fillOpacity: 0.3 }) },
      })
    },
  }), [zones])

  useEffect(() => {
    layer.addTo(map)
    const bounds = layer.getBounds()
    if (bounds.isValid()) map.fitBounds(bounds, { padding: [24, 24], maxZoom: 15 })
    return () => { map.removeLayer(layer) }
  }, [layer, map])
  return null
}

export function DeliveryZonesPage() {
  const [zones, setZones] = useState<ZoneCollection>({ type: 'FeatureCollection', features: [] })
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    let active = true
    api.get<ZoneCollection>('/zonas-entrega')
      .then(({ data }) => { if (active) setZones(data) })
      .catch((reason: unknown) => { if (active) setError(errorMessage(reason, 'Não foi possível carregar as zonas de entrega.')) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  async function importFile(file?: File) {
    if (!file) return
    setError('')
    setNotice('')
    setUploading(true)
    try {
      const collection = JSON.parse(await file.text()) as ZoneCollection
      if (collection.type !== 'FeatureCollection' || !Array.isArray(collection.features)) throw new Error('O arquivo deve conter um GeoJSON FeatureCollection.')
      await api.post<ZoneCollection>('/zonas-entrega/importar-geojson', collection)
      const { data } = await api.get<ZoneCollection>('/zonas-entrega')
      setZones(data)
      setNotice(`${collection.features.length} zona${collection.features.length === 1 ? '' : 's'} importada${collection.features.length === 1 ? '' : 's'} com sucesso.`)
    } catch (reason: unknown) {
      setError(reason instanceof SyntaxError ? 'O arquivo selecionado não contém um JSON válido.' : errorMessage(reason, reason instanceof Error ? reason.message : 'Não foi possível importar o GeoJSON.'))
    } finally { setUploading(false) }
  }

  async function removeZone(name: string) {
    setError('')
    try {
      await api.delete(`/zonas-entrega/${encodeURIComponent(name)}`)
      setZones((current) => ({ ...current, features: current.features.filter((feature) => feature.properties.nome !== name) }))
      setNotice(`Zona "${name}" removida.`)
    } catch (reason: unknown) { setError(errorMessage(reason, `Não foi possível remover a zona ${name}.`)) }
  }

  return <div>
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4"><div><p className="mb-2 text-xs font-bold tracking-[0.2em] text-urucum">LOGÍSTICA</p><h1 className="mb-2 text-3xl font-bold tracking-tight text-cafe">Zonas de entrega</h1><p className="text-sm text-cafe-suave">Consulte as áreas e importe zonas de taxa a partir de GeoJSON.</p></div>
      <label className={`cursor-pointer rounded-xl bg-urucum px-5 py-3 text-sm font-semibold text-white transition hover:bg-urucum-escuro ${uploading ? 'pointer-events-none opacity-60' : ''}`}>{uploading ? 'Importando...' : 'Importar GeoJSON'}<input accept=".geojson,.json,application/geo+json,application/json" className="sr-only" disabled={uploading} onChange={(event) => { void importFile(event.target.files?.[0]); event.currentTarget.value = '' }} type="file" /></label>
    </div>
    <div className="mb-4 rounded-xl border border-milho/40 bg-milho/10 p-4 text-sm text-cafe"><strong>Formato:</strong> envie um GeoJSON <code>FeatureCollection</code> com polígonos e propriedades <code>nome</code> (ou <code>zona</code>) e <code>valor</code> (ou <code>taxa</code>). Zonas com o mesmo nome são atualizadas.</div>
    {error && <div className="mb-4 rounded-xl border border-urucum/20 bg-urucum/5 px-4 py-3 text-sm text-urucum-escuro" role="alert">{error}</div>}
    {notice && <div className="mb-4 rounded-xl border border-milho/40 bg-milho/10 px-4 py-3 text-sm text-cafe" role="status">{notice}</div>}
    <section className="overflow-hidden rounded-2xl border border-cafe-suave/15 bg-white shadow-sm"><div className="h-[520px] w-full"><MapContainer center={[-7.12, -34.88]} zoom={12} className="h-full w-full" scrollWheelZoom><TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />{zones.features.length > 0 && <ZoneLayers zones={zones} />}</MapContainer></div></section>
    <section className="mt-6 rounded-2xl border border-cafe-suave/15 bg-white p-5 shadow-sm"><div className="mb-4 flex items-center justify-between"><div><h2 className="font-bold text-cafe">Áreas cadastradas</h2><p className="text-xs text-cafe-suave">Passe o mouse sobre uma área no mapa para consultar a taxa.</p></div><span className="rounded-full bg-tapioca px-3 py-1 text-xs font-semibold text-cafe-suave">{zones.features.length} zonas</span></div>
      {loading ? <p className="py-6 text-center text-sm text-cafe-suave">Carregando zonas...</p> : zones.features.length === 0 ? <p className="py-6 text-center text-sm text-cafe-suave">Nenhuma zona cadastrada. Importe um arquivo GeoJSON para começar.</p> : <ul className="divide-y divide-cafe-suave/10">{zones.features.map((feature, index) => <li className="flex items-center justify-between gap-4 py-3" key={`${feature.properties.nome}-${index}`}><div><p className="font-semibold text-cafe">{feature.properties.nome}</p><p className="text-sm text-cafe-suave">{new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(feature.properties.valor)}</p></div><button className="rounded-lg px-3 py-2 text-xs font-semibold text-urucum-escuro hover:bg-urucum/5" onClick={() => { void removeZone(feature.properties.nome) }} type="button">Remover</button></li>)}</ul>}
    </section>
  </div>
}
