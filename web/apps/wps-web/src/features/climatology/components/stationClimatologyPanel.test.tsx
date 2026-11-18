import { fireEvent, render, screen } from '@testing-library/react'
import { getStations } from '@wps/api/stationAPI'
import type { GeoJsonStation } from '@wps/types/stationTypes'
import { Provider } from 'react-redux'
import type { Mock } from 'vitest'
import type { ClimatologyViewProps } from '@/features/climatology/components/ClimatologyView'
import type { StationClimatologyMapProps } from '@/features/climatology/components/map/StationClimatologyMap'
import { createTestStore } from '@/test/testUtils'
import StationClimatologyPanel from './StationClimatologyPanel'

vi.mock('@wps/api/stationAPI', async importOriginal => ({
  ...(await importOriginal<typeof import('@wps/api/stationAPI')>()),
  getStations: vi.fn()
}))

// The map needs a laid-out page, which jsdom does not have. Its stand-in offers the choices a
// click and a drawn area make.
vi.mock('@/features/climatology/components/map/StationClimatologyMap', () => ({
  default: ({ stations, chosenCodes, onChoose }: StationClimatologyMapProps) => (
    <div data-testid="station-map" data-stations={stations.length} data-chosen={chosenCodes.join(',')}>
      <button type="button" onClick={() => onChoose([322], null)}>
        Click AFTON
      </button>
      <button type="button" onClick={() => onChoose([322, 209, 999], '3 stations in the drawn area')}>
        Draw around three
      </button>
    </div>
  )
}))

vi.mock('@/features/climatology/components/ClimatologyView', () => ({
  default: ({ stations, groupLabel, emptyMessage }: ClimatologyViewProps) => (
    <div
      data-testid="climatology-view"
      data-stations={stations.map(station => `${station.code}:${station.name}`).join(',')}
      data-label={groupLabel ?? ''}
    >
      {stations.length === 0 && emptyMessage}
    </div>
  )
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

const renderPanel = () =>
  render(
    <Provider store={createTestStore()}>
      <StationClimatologyPanel />
    </Provider>
  )

describe('StationClimatologyPanel', () => {
  beforeEach(() => {
    ;(getStations as Mock).mockResolvedValue([station(322, 'AFTON'), station(209, 'ALEXIS CREEK')])
  })

  it('maps every station and says how to choose them', async () => {
    renderPanel()

    expect(await screen.findByTestId('station-map')).toHaveAttribute('data-stations', '2')
    expect(screen.getByText(/Click a station on the map, or draw an area/)).toBeInTheDocument()
  })

  it('charts the station clicked', async () => {
    renderPanel()
    await screen.findByTestId('station-map')

    fireEvent.click(screen.getByRole('button', { name: 'Click AFTON' }))

    expect(screen.getByTestId('climatology-view')).toHaveAttribute('data-stations', '322:AFTON')
    expect(screen.getByTestId('climatology-view')).toHaveAttribute('data-label', '')
    expect(screen.getByTestId('station-map')).toHaveAttribute('data-chosen', '322')
  })

  it('charts the stations in a drawn area under its name', async () => {
    renderPanel()
    await screen.findByTestId('station-map')
    await screen.findByText(/Click a station/)

    fireEvent.click(screen.getByRole('button', { name: 'Draw around three' }))

    // A station the list does not name is shown by its code.
    expect(screen.getByTestId('climatology-view')).toHaveAttribute(
      'data-stations',
      '322:AFTON,209:ALEXIS CREEK,999:999'
    )
    expect(screen.getByTestId('climatology-view')).toHaveAttribute('data-label', '3 stations in the drawn area')
  })
})
