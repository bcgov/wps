import { fireEvent, render, screen } from '@testing-library/react'
import type { GeoJsonStation } from '@wps/types/stationTypes'
import { containsCoordinate } from 'ol/extent'
import { fromLonLat } from 'ol/proj'
import StationClimatologyMap, { stationsExtent } from './StationClimatologyMap'

vi.mock('@wps/utils/vectorLayerUtils', () => ({
  getStyleJson: vi.fn().mockRejectedValue(new Error('No base map in tests')),
  createVectorTileLayer: vi.fn()
}))

vi.mock('@/features/map/fireCentreLayer', async () => {
  const { default: VectorLayer } = await import('ol/layer/Vector')
  return { getFireCentreLinePMTilesLayer: vi.fn(() => new VectorLayer()) }
})

vi.mock('@wps/utils/error', () => ({ logError: vi.fn() }))

class ResizeObserver {
  observe() {
    // mock no-op
  }
  unobserve() {
    // mock no-op
  }
  disconnect() {
    // mock no-op
  }
}
globalThis.ResizeObserver = ResizeObserver

const stations: GeoJsonStation[] = [
  {
    type: 'Feature',
    properties: {
      code: 322,
      name: 'AFTON',
      ecodivision_name: null,
      core_season: { start_month: 5, start_day: 1, end_month: 9, end_day: 15 }
    },
    geometry: { type: 'Point', coordinates: [-120, 50] }
  }
]

// Clicking and drawing on the map need a laid-out page, so they are checked in a browser; the
// choices they make are tested in stationSelection.test.ts.
describe('StationClimatologyMap', () => {
  it('starts with clicking stations, and switches to drawing an area', () => {
    render(<StationClimatologyMap stations={stations} chosenCodes={[]} onChoose={vi.fn()} />)

    expect(screen.getByText(/Click a station to chart it/)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Draw an area' }))

    expect(screen.getByText(/double-click to finish/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Draw an area' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('draws an outline by its corners or freehand, with a point to undo', () => {
    render(<StationClimatologyMap stations={stations} chosenCodes={[]} onChoose={vi.fn()} />)
    expect(screen.queryByRole('button', { name: 'Undo point' })).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Draw an area' }))

    expect(screen.getByRole('button', { name: 'Undo point' })).toBeInTheDocument()
    expect(screen.getByText(/Click to add corners and double-click to finish, or hold Shift/)).toBeInTheDocument()
    // Undo with nothing drawn yet does nothing, and does not fail.
    fireEvent.click(screen.getByRole('button', { name: 'Undo point' }))
  })

  it('clears the stations chosen', () => {
    const onChoose = vi.fn()
    const { rerender } = render(<StationClimatologyMap stations={stations} chosenCodes={[]} onChoose={onChoose} />)
    expect(screen.getByRole('button', { name: 'Clear' })).toBeDisabled()

    rerender(<StationClimatologyMap stations={stations} chosenCodes={[322]} onChoose={onChoose} />)
    fireEvent.click(screen.getByRole('button', { name: 'Clear' }))

    expect(onChoose).toHaveBeenCalledWith([], null)
  })

  it('covers BC and stations outside it', () => {
    const yukon = {
      ...stations[0],
      properties: { ...stations[0].properties, code: 964, name: 'HAINES JUNCTION YFS' },
      geometry: { type: 'Point', coordinates: [-137.576167, 60.77295] }
    }

    const extent = stationsExtent([...stations, yukon])

    expect(containsCoordinate(extent, fromLonLat([-137.576167, 60.77295]))).toBe(true)
    expect(containsCoordinate(extent, fromLonLat([-125, 54.5]))).toBe(true)
    expect(containsCoordinate(stationsExtent([]), fromLonLat([-137.576167, 60.77295]))).toBe(false)
  })
})
