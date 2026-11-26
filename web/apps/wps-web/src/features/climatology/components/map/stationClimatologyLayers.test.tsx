import { fireEvent, render, screen } from '@testing-library/react'
import type { GeoJsonStation } from '@wps/types/stationTypes'
import { Map as OlMap, View } from 'ol'
import { containsCoordinate } from 'ol/extent'
import { fromLonLat } from 'ol/proj'
import { useSfmsMap } from '@/features/sfmsInsights/components/map/SFMSMap'
import StationClimatologyLayers, { stationsExtent } from './StationClimatologyLayers'

vi.mock('@/features/sfmsInsights/components/map/SFMSMap', () => ({ useSfmsMap: vi.fn() }))

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
describe('StationClimatologyLayers', () => {
  let map: OlMap
  const atlantic = fromLonLat([-30, 40])

  beforeEach(() => {
    map = new OlMap({ target: document.createElement('div'), view: new View({ center: atlantic, resolution: 1000 }) })
    vi.mocked(useSfmsMap).mockReturnValue(map)
  })

  it('puts the stations on the map while shown, and takes them off after', () => {
    const { unmount } = render(<StationClimatologyLayers stations={stations} chosenCodes={[]} onChoose={vi.fn()} />)

    expect(map.getLayers().getLength()).toBe(2)
    // The map is fitted to BC and the stations, and panning stops a margin past them.
    expect(containsCoordinate(stationsExtent(stations), map.getView().getCenter() ?? [])).toBe(true)
    expect(map.getView().getConstrainedCenter(atlantic)).not.toEqual(atlantic)

    unmount()

    expect(map.getLayers().getLength()).toBe(0)
    expect(containsCoordinate(stationsExtent([]), map.getView().getCenter() ?? [])).toBe(true)
    expect(map.getView().getConstrainedCenter(atlantic)).toEqual(atlantic)
  })

  it('starts with clicking stations, and switches to drawing an area', () => {
    render(<StationClimatologyLayers stations={stations} chosenCodes={[]} onChoose={vi.fn()} />)

    expect(screen.getByText(/Click a station to chart it/)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Draw an area' }))

    expect(screen.getByText(/double-click to finish/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Draw an area' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('draws an outline by its corners or freehand, with a point to undo', () => {
    render(<StationClimatologyLayers stations={stations} chosenCodes={[]} onChoose={vi.fn()} />)
    expect(screen.queryByRole('button', { name: 'Undo point' })).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Draw an area' }))

    expect(screen.getByRole('button', { name: 'Undo point' })).toBeInTheDocument()
    expect(screen.getByText(/Click to add corners and double-click to finish, or hold Shift/)).toBeInTheDocument()
    // Undo with nothing drawn yet does nothing, and does not fail.
    fireEvent.click(screen.getByRole('button', { name: 'Undo point' }))
  })

  it('clears the stations chosen', () => {
    const onChoose = vi.fn()
    const { rerender } = render(<StationClimatologyLayers stations={stations} chosenCodes={[]} onChoose={onChoose} />)
    expect(screen.getByRole('button', { name: 'Clear' })).toBeDisabled()

    rerender(<StationClimatologyLayers stations={stations} chosenCodes={[322]} onChoose={onChoose} />)
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

  it('leaves out stations far from BC, which are most likely misplaced', () => {
    const misplaced = (code: number, coordinates: number[]) => ({
      ...stations[0],
      properties: { ...stations[0].properties, code },
      geometry: { type: 'Point', coordinates }
    })

    const extent = stationsExtent([...stations, misplaced(1, [0, 0]), misplaced(2, [120, 50]), misplaced(3, [-60, 45])])

    expect(extent).toEqual(stationsExtent([]))
  })
})
