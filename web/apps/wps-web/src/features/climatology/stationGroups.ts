import type { ClimatologyFireCentre } from '@wps/api/climatologyAPI'
import type { StationGroup } from '@wps/api/stationAPI'
import { sortBy } from 'lodash'

export interface StationOption {
  code: number
  name: string
}

// A set of stations to choose all at once. A saved group's stations are fetched when it is
// chosen, so it has none until then.
export type GroupOption =
  | { kind: 'fire-centre'; label: string; stations: StationOption[] }
  | { kind: 'fire-zone'; label: string; stations: StationOption[] }
  | { kind: 'saved'; label: string; groupId: string }

export const GROUP_KIND_LABELS: Record<GroupOption['kind'], string> = {
  'fire-centre': 'Fire centres',
  'fire-zone': 'Fire zones',
  saved: 'Your station groups'
}

/** Every fire centre, every fire zone and every saved group, as groups to choose from. */
export const groupOptions = (fireCentres: ClimatologyFireCentre[], savedGroups: StationGroup[]): GroupOption[] => {
  const centres: GroupOption[] = fireCentres.map(centre => ({
    kind: 'fire-centre',
    label: centre.name,
    stations: centre.stations.map(({ code, name }) => ({ code, name }))
  }))
  const zones = new Map<string, { centre: string; stations: StationOption[] }>()
  for (const centre of fireCentres) {
    for (const station of centre.stations) {
      if (station.zone) {
        const zone = zones.get(station.zone) ?? { centre: centre.name, stations: [] }
        zone.stations.push({ code: station.code, name: station.name })
        zones.set(station.zone, zone)
      }
    }
  }
  const zoneOptions: GroupOption[] = sortBy([...zones.entries()], ([zone]) => zone).map(
    ([zone, { centre, stations }]) => ({
      kind: 'fire-zone',
      label: `${zone}, ${centre}`,
      stations
    })
  )
  const saved: GroupOption[] = sortBy(savedGroups, group => group.display_label).map(group => ({
    kind: 'saved',
    label: group.display_label,
    groupId: group.id
  }))
  return [...centres, ...zoneOptions, ...saved]
}
