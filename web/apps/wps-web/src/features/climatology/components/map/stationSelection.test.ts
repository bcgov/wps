import type { GeoJsonStation } from '@wps/types/stationTypes'
import { Circle, Polygon } from 'ol/geom'
import { fromExtent } from 'ol/geom/Polygon'
import { fromLonLat } from 'ol/proj'
import { areaLabel, clickStation, stationsInArea } from './stationSelection'

const station = (code: number, lon: number, lat: number): GeoJsonStation => ({
  type: 'Feature',
  properties: {
    code,
    name: `S${code}`,
    ecodivision_name: null,
    core_season: { start_month: 5, start_day: 1, end_month: 9, end_day: 15 }
  },
  geometry: { type: 'Point', coordinates: [lon, lat] }
})

describe('stationsInArea', () => {
  it('is the stations inside the drawn outline', () => {
    const area = new Polygon([
      [
        [-121, 49],
        [-119, 49],
        [-119, 51],
        [-121, 51],
        [-121, 49]
      ].map(([lon, lat]) => fromLonLat([lon, lat]))
    ])
    const stations = [station(1, -120, 50), station(2, -118, 50), station(3, -120.5, 50.9), station(4, -120, 52)]

    expect(stationsInArea(stations, area)).toEqual([1, 3])
  })

  it('is the stations inside a box or a circle', () => {
    const stations = [station(1, -120, 50), station(2, -118, 50), station(3, -120.5, 50.9)]
    const [west, south] = fromLonLat([-121, 49])
    const [east, north] = fromLonLat([-119, 51])

    expect(stationsInArea(stations, fromExtent([west, south, east, north]))).toEqual([1, 3])
    // A circle around station 1 small enough to leave out station 3, 100 km away.
    expect(stationsInArea(stations, new Circle(fromLonLat([-120, 50]), 50_000))).toEqual([1])
  })
})

describe('clickStation', () => {
  it('chooses only the station clicked', () => {
    expect(clickStation([1, 2], 3, false)).toEqual([3])
  })

  it('adds or removes the station with Shift', () => {
    expect(clickStation([1, 2], 3, true)).toEqual([1, 2, 3])
    expect(clickStation([1, 2], 2, true)).toEqual([1])
  })
})

describe('areaLabel', () => {
  it('counts the stations', () => {
    expect(areaLabel(1)).toBe('1 station in the drawn area')
    expect(areaLabel(12)).toBe('12 stations in the drawn area')
  })
})
