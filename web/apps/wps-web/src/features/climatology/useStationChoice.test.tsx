import { act, renderHook, waitFor } from '@testing-library/react'
import { getStations } from '@wps/api/stationAPI'
import type { GeoJsonStation } from '@wps/types/stationTypes'
import type { ReactNode } from 'react'
import { Provider } from 'react-redux'
import type { Mock } from 'vitest'
import { createTestStore } from '@/test/testUtils'
import { useStationChoice } from './useStationChoice'

vi.mock('@wps/api/stationAPI', async importOriginal => ({
  ...(await importOriginal<typeof import('@wps/api/stationAPI')>()),
  getStations: vi.fn()
}))

const station = (code: number, name: string): GeoJsonStation => ({
  type: 'Feature',
  properties: {
    code,
    name,
    ecodivision_name: null,
    core_season: { start_month: 5, start_day: 1, end_month: 9, end_day: 15 }
  },
  geometry: { type: 'Point', coordinates: [-120, 50] }
})

const renderChoice = (enabled: boolean) => {
  const store = createTestStore()
  const wrapper = ({ children }: { children: ReactNode }) => <Provider store={store}>{children}</Provider>
  return renderHook(({ on }) => useStationChoice(on), { wrapper, initialProps: { on: enabled } })
}

describe('useStationChoice', () => {
  beforeEach(() => {
    ;(getStations as Mock).mockReset()
    ;(getStations as Mock).mockResolvedValue([station(322, 'AFTON'), station(209, 'ALEXIS CREEK')])
  })

  it('loads the stations once, when first enabled', async () => {
    const { result, rerender } = renderChoice(false)
    expect(getStations).not.toHaveBeenCalled()

    rerender({ on: true })
    await waitFor(() => expect(result.current.stations).toHaveLength(2))
    rerender({ on: false })
    rerender({ on: true })

    expect(getStations).toHaveBeenCalledTimes(1)
  })

  it('names the stations clicked', async () => {
    const { result } = renderChoice(true)
    await waitFor(() => expect(result.current.stations).toHaveLength(2))

    act(() => result.current.onChoose([322], null))

    expect(result.current.chosenCodes).toEqual([322])
    expect(result.current.chosen).toEqual([{ code: 322, name: 'AFTON' }])
    expect(result.current.label).toBeNull()
  })

  it('names the stations in a drawn area, and the area', async () => {
    const { result } = renderChoice(true)
    await waitFor(() => expect(result.current.stations).toHaveLength(2))

    act(() => result.current.onChoose([322, 209, 999], '3 stations in the drawn area'))

    // A station the list does not name is shown by its code.
    expect(result.current.chosen.map(({ name }) => name)).toEqual(['AFTON', 'ALEXIS CREEK', '999'])
    expect(result.current.label).toBe('3 stations in the drawn area')
  })
})
