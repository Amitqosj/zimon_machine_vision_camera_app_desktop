import type { ZimonProtocol } from '../../types/zimonProtocol'
import { newProtocolId } from '../../types/zimonProtocol'

const KEY = 'zimon-protocol-library-v1'

function readRaw(): unknown {
  try {
    const s = localStorage.getItem(KEY)
    if (!s) return []
    return JSON.parse(s)
  } catch {
    return []
  }
}

export function loadProtocolLibrary(): ZimonProtocol[] {
  const raw = readRaw()
  if (!Array.isArray(raw)) return []
  return raw.filter(
    (x): x is ZimonProtocol =>
      x &&
      typeof x === 'object' &&
      typeof (x as ZimonProtocol).id === 'string' &&
      typeof (x as ZimonProtocol).name === 'string' &&
      Array.isArray((x as ZimonProtocol).phases),
  )
}

export function saveProtocolLibrary(items: ZimonProtocol[]) {
  try {
    localStorage.setItem(KEY, JSON.stringify(items))
  } catch {
    /* quota */
  }
}

export function upsertProtocol(p: ZimonProtocol) {
  const all = loadProtocolLibrary()
  const i = all.findIndex((x) => x.id === p.id)
  const next = { ...p, updatedAt: new Date().toISOString() }
  if (i >= 0) all[i] = next
  else all.push(next)
  saveProtocolLibrary(all)
}

export function deleteProtocolFromLibrary(id: string) {
  saveProtocolLibrary(loadProtocolLibrary().filter((x) => x.id !== id))
}

export function duplicateProtocol(source: ZimonProtocol): ZimonProtocol {
  return {
    ...source,
    id: newProtocolId(),
    name: `${source.name} (copy)`,
    updatedAt: new Date().toISOString(),
  }
}
