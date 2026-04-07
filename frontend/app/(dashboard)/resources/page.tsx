"use client"

import { useEffect, useState } from "react"
import { getToken } from "@/lib/auth"
import {
  getServices, createService, deleteService,
  getResources, createResource, deleteResource,
  type ServiceData, type ResourceData,
} from "@/lib/api"
import { Plus, Trash2, BedDouble, UtensilsCrossed, Clock, Box, ChevronDown, ChevronUp, Store } from "lucide-react"

const NICHE_OPTIONS = [
  { value: "restaurant", label: "Restaurante", icon: UtensilsCrossed, defaultType: "table", defaultCapacity: 4, defaultDuration: 90 },
  { value: "hotel", label: "Hotel", icon: BedDouble, defaultType: "room", defaultCapacity: 2, defaultDuration: 1440 },
  { value: "agenda", label: "Agenda / Citas", icon: Clock, defaultType: "slot", defaultCapacity: 1, defaultDuration: 60 },
  { value: "custom", label: "Personalizado", icon: Box, defaultType: "custom", defaultCapacity: 1, defaultDuration: 60 },
]

const TYPE_ICONS: Record<string, typeof Box> = {
  table: UtensilsCrossed, room: BedDouble, slot: Clock, custom: Box,
}

export default function ResourcesPage() {
  const [services, setServices] = useState<ServiceData[]>([])
  const [resources, setResources] = useState<ResourceData[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedService, setExpandedService] = useState<string | null>(null)
  const [showServiceForm, setShowServiceForm] = useState(false)
  const [serviceForm, setServiceForm] = useState({ name: "", niche: "restaurant", description: "" })
  const [addingResourceTo, setAddingResourceTo] = useState<string | null>(null)
  const [resourceForm, setResourceForm] = useState({ name: "", resource_type: "table", capacity: 4, duration_minutes: 90, description: "" })

  const token = getToken() || ""

  async function loadAll() {
    try {
      const [svcs, res] = await Promise.all([getServices(token), getResources(token)])
      setServices(svcs)
      setResources(res)
      if (svcs.length > 0 && !expandedService) setExpandedService(svcs[0].id)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  useEffect(() => { if (token) loadAll() }, [token])

  async function handleCreateService() {
    try {
      const svc = await createService(token, serviceForm)
      setShowServiceForm(false)
      setServiceForm({ name: "", niche: "restaurant", description: "" })
      setExpandedService(svc.id)
      loadAll()
    } catch (e: any) { alert(e.message) }
  }

  async function handleDeleteService(id: string) {
    if (!confirm("Eliminar este servicio y todos sus recursos?")) return
    try { await deleteService(token, id); loadAll() }
    catch (e: any) { alert(e.message) }
  }

  async function handleCreateResource(serviceId: string) {
    try {
      await createResource(token, { ...resourceForm, service_id: serviceId })
      setAddingResourceTo(null)
      setResourceForm({ name: "", resource_type: "table", capacity: 4, duration_minutes: 90, description: "" })
      loadAll()
    } catch (e: any) { alert(e.message) }
  }

  async function handleDeleteResource(id: string) {
    if (!confirm("Eliminar este recurso?")) return
    try { await deleteResource(token, id); loadAll() }
    catch (e: any) { alert(e.message) }
  }

  function onNicheChange(niche: string) {
    const opt = NICHE_OPTIONS.find((o) => o.value === niche)
    setServiceForm({ ...serviceForm, niche })
    if (opt) {
      setResourceForm((f) => ({ ...f, resource_type: opt.defaultType, capacity: opt.defaultCapacity, duration_minutes: opt.defaultDuration }))
    }
  }

  if (loading) return <div className="animate-pulse text-gray-400">Cargando...</div>

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Servicios y Recursos</h1>
          <p className="text-sm text-gray-500">Primero crea un servicio, luego agrega sus recursos</p>
        </div>
        <button
          onClick={() => setShowServiceForm(!showServiceForm)}
          className="flex items-center gap-2 bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700 transition"
        >
          <Plus className="w-4 h-4" /> Nuevo servicio
        </button>
      </div>

      {/* Form crear servicio */}
      {showServiceForm && (
        <div className="bg-white p-6 rounded-xl border border-gray-100 mb-6 space-y-4">
          <h3 className="font-semibold text-sm">Crear servicio</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Nombre del servicio</label>
              <input
                value={serviceForm.name}
                onChange={(e) => setServiceForm({ ...serviceForm, name: e.target.value })}
                placeholder="ej: Restaurant Il Giardino"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Tipo de servicio</label>
              <div className="grid grid-cols-2 gap-2">
                {NICHE_OPTIONS.map((opt) => {
                  const Icon = opt.icon
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => onNicheChange(opt.value)}
                      className={`flex items-center gap-2 p-2 rounded-lg border text-xs transition ${
                        serviceForm.niche === opt.value
                          ? "border-brand-500 bg-brand-50 text-brand-700"
                          : "border-gray-200 text-gray-600 hover:border-gray-300"
                      }`}
                    >
                      <Icon className="w-4 h-4" /> {opt.label}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleCreateService} className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700">
              Crear servicio
            </button>
            <button onClick={() => setShowServiceForm(false)} className="text-gray-500 px-4 py-2 text-sm hover:text-gray-700">
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Lista de servicios */}
      {services.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-100 p-12 text-center">
          <Store className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-1">No hay servicios configurados</p>
          <p className="text-sm text-gray-400">Crea un servicio (restaurante, hotel, agenda) y luego agrega sus recursos</p>
        </div>
      ) : (
        <div className="space-y-4">
          {services.map((svc) => {
            const isExpanded = expandedService === svc.id
            const svcResources = resources.filter((r) => r.service_id === svc.id)
            const nicheOpt = NICHE_OPTIONS.find((o) => o.value === svc.niche) || NICHE_OPTIONS[3]
            const NicheIcon = nicheOpt.icon

            return (
              <div key={svc.id} className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                {/* Header del servicio */}
                <div
                  className="flex items-center justify-between p-5 cursor-pointer hover:bg-gray-50 transition"
                  onClick={() => setExpandedService(isExpanded ? null : svc.id)}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-brand-50 text-brand-600 rounded-lg flex items-center justify-center">
                      <NicheIcon className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-sm">{svc.name}</h3>
                      <p className="text-xs text-gray-500">{nicheOpt.label} &middot; {svc.resource_count} recursos</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteService(svc.id) }}
                      className="text-gray-300 hover:text-red-500 transition p-1"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                  </div>
                </div>

                {/* Recursos del servicio */}
                {isExpanded && (
                  <div className="border-t border-gray-50 p-5 bg-gray-50/50">
                    {svcResources.length > 0 && (
                      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
                        {svcResources.map((r) => {
                          const Icon = TYPE_ICONS[r.resource_type] || Box
                          return (
                            <div key={r.id} className="bg-white p-4 rounded-lg border border-gray-100 flex items-start justify-between">
                              <div className="flex items-start gap-2">
                                <Icon className="w-4 h-4 text-gray-400 mt-0.5" />
                                <div>
                                  <p className="font-medium text-sm">{r.name}</p>
                                  <p className="text-xs text-gray-500">{r.capacity} pers. &middot; {r.duration_minutes} min</p>
                                  {r.description && <p className="text-xs text-gray-400 mt-0.5">{r.description}</p>}
                                </div>
                              </div>
                              <button onClick={() => handleDeleteResource(r.id)} className="text-gray-300 hover:text-red-500">
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          )
                        })}
                      </div>
                    )}

                    {/* Form agregar recurso */}
                    {addingResourceTo === svc.id ? (
                      <div className="bg-white p-4 rounded-lg border border-gray-200 space-y-3">
                        <div className="grid grid-cols-3 gap-3">
                          <input
                            value={resourceForm.name}
                            onChange={(e) => setResourceForm({ ...resourceForm, name: e.target.value })}
                            placeholder={svc.niche === "restaurant" ? "Mesa 1" : svc.niche === "hotel" ? "Suite Superior" : "Hora 09:00"}
                            className="px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500"
                          />
                          <input
                            type="number" min={1}
                            value={resourceForm.capacity}
                            onChange={(e) => setResourceForm({ ...resourceForm, capacity: parseInt(e.target.value) || 1 })}
                            className="px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500"
                            placeholder="Capacidad"
                          />
                          <input
                            type="number" min={15} step={15}
                            value={resourceForm.duration_minutes}
                            onChange={(e) => setResourceForm({ ...resourceForm, duration_minutes: parseInt(e.target.value) || 60 })}
                            className="px-3 py-2 border border-gray-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-brand-500"
                            placeholder="Duracion (min)"
                          />
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleCreateResource(svc.id)}
                            className="bg-brand-600 text-white px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-brand-700"
                          >
                            Agregar
                          </button>
                          <button
                            onClick={() => setAddingResourceTo(null)}
                            className="text-gray-500 px-3 py-1.5 text-xs hover:text-gray-700"
                          >
                            Cancelar
                          </button>
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => {
                          setAddingResourceTo(svc.id)
                          setResourceForm({
                            name: "", resource_type: nicheOpt.defaultType,
                            capacity: nicheOpt.defaultCapacity,
                            duration_minutes: nicheOpt.defaultDuration,
                            description: "",
                          })
                        }}
                        className="flex items-center gap-1 text-brand-600 text-xs font-medium hover:text-brand-700"
                      >
                        <Plus className="w-3.5 h-3.5" /> Agregar recurso
                      </button>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
