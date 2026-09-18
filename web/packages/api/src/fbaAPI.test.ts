import { vi } from 'vitest'
import axios from './axios'
import { getFireCentreTPIStats } from './fbaAPI'
import { RunType } from './runType'

describe('fbaAPI', () => {
  it('places the for date before the run datetime in the fire-centre TPI URL', async () => {
    const response = {
      fire_centre_name: 'Cariboo Fire Centre',
      firezone_tpi_stats: []
    }
    axios.get = vi.fn().mockResolvedValue({ data: response })

    const result = await getFireCentreTPIStats(
      'Cariboo Fire Centre',
      RunType.FORECAST,
      '2025-08-26',
      '2025-08-25T18:00:00Z'
    )

    expect(axios.get).toHaveBeenCalledWith(
      'fba/fire-centre-tpi-stats/forecast/2025-08-26/2025-08-25T18:00:00Z/Cariboo Fire Centre'
    )
    expect(result).toEqual(response)
  })
})
