import { vi } from 'vitest'
import axios from './axios'
import { type DailyClimatology, getClimatologyFireCentres, getDailyClimatology } from './climatologyAPI'

describe('climatologyAPI', () => {
  it('requests stations, a variable, a year, a method and years to compare, and returns the response', async () => {
    const climatology: DailyClimatology = { variable: 'temperature', year: 2026, method: 'pooled', series: [] }
    axios.get = vi.fn().mockResolvedValue({ data: climatology })

    const result = await getDailyClimatology([322, 209], 'temperature', 2026, 'pooled', [2025, 2017])

    expect(axios.get).toHaveBeenCalledWith('/climatology/daily', {
      params: {
        station_codes: [322, 209],
        variable: 'temperature',
        year: 2026,
        method: 'pooled',
        compare_years: [2025, 2017]
      },
      paramsSerializer: { indexes: null }
    })
    expect(result).toEqual(climatology)
  })

  it('sends the stations as a repeated parameter', () => {
    const url = axios.getUri({
      url: '/climatology/daily',
      params: { station_codes: [322, 209] },
      paramsSerializer: { indexes: null }
    })

    expect(url).toContain('station_codes=322&station_codes=209')
  })

  it('returns the fire centres', async () => {
    const centres = [{ id: 2, name: 'Kamloops Fire Centre', stations: [{ code: 322, name: 'SPARKS', zone: 'K2' }] }]
    axios.get = vi.fn().mockResolvedValue({ data: { fire_centres: centres } })

    expect(await getClimatologyFireCentres()).toEqual(centres)
    expect(axios.get).toHaveBeenCalledWith('/climatology/fire-centres')
  })
})
