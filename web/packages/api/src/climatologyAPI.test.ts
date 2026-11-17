import { vi } from 'vitest'
import axios from './axios'
import { type DailyClimatology, getDailyClimatology } from './climatologyAPI'

describe('climatologyAPI', () => {
  it('requests a station, variable and year, and returns the response', async () => {
    const climatology: DailyClimatology = {
      station_code: 322,
      variable: 'temperature',
      year: 2026,
      first_reference_year: 1990,
      last_reference_year: 2025,
      days: [],
      observations: []
    }
    axios.get = vi.fn().mockResolvedValue({ data: climatology })

    const result = await getDailyClimatology(322, 'temperature', 2026)

    expect(axios.get).toHaveBeenCalledWith('/climatology/stations/322/daily', {
      params: { variable: 'temperature', year: 2026 }
    })
    expect(result).toEqual(climatology)
  })
})
