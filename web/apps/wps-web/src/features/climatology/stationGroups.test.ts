import type { ClimatologyFireCentre } from '@wps/api/climatologyAPI'
import type { StationGroup } from '@wps/api/stationAPI'
import { groupOptions } from './stationGroups'

const centres: ClimatologyFireCentre[] = [
  {
    id: 2,
    name: 'Kamloops Fire Centre',
    stations: [
      { code: 322, name: 'AFTON', zone: 'K2' },
      { code: 209, name: 'ALEXIS CREEK', zone: 'K4' },
      { code: 400, name: 'BLUE RIVER', zone: 'K2' },
      { code: 401, name: 'NO ZONE', zone: null }
    ]
  },
  { id: 3, name: 'Cariboo Fire Centre', stations: [{ code: 500, name: 'BIG CREEK', zone: 'C1' }] }
]

const saved: StationGroup[] = [
  {
    id: 'b',
    display_label: 'Zeballos test',
    group_description: null,
    group_owner_user_guid: '',
    group_owner_user_id: ''
  },
  { id: 'a', display_label: 'My valleys', group_description: null, group_owner_user_guid: '', group_owner_user_id: '' }
]

describe('groupOptions', () => {
  const options = groupOptions(centres, saved)

  it('offers fire centres, then fire zones, then saved groups', () => {
    expect(options.map(option => [option.kind, option.label])).toEqual([
      ['fire-centre', 'Kamloops Fire Centre'],
      ['fire-centre', 'Cariboo Fire Centre'],
      ['fire-zone', 'C1, Cariboo Fire Centre'],
      ['fire-zone', 'K2, Kamloops Fire Centre'],
      ['fire-zone', 'K4, Kamloops Fire Centre'],
      ['saved', 'My valleys'],
      ['saved', 'Zeballos test']
    ])
  })

  it('gives a fire centre all its stations, and a zone the stations in it', () => {
    const kamloops = options[0]
    const k2 = options.find(option => option.label.startsWith('K2'))

    expect(kamloops.kind === 'fire-centre' && kamloops.stations.map(station => station.code)).toEqual([
      322, 209, 400, 401
    ])
    expect(k2?.kind === 'fire-zone' && k2.stations).toEqual([
      { code: 322, name: 'AFTON' },
      { code: 400, name: 'BLUE RIVER' }
    ])
  })

  it('keeps a saved group to fetch its stations when chosen', () => {
    expect(options.find(option => option.kind === 'saved')).toEqual({
      kind: 'saved',
      label: 'My valleys',
      groupId: 'a'
    })
  })
})
