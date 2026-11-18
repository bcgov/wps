import type { GeoJsonStation } from '@wps/types/stationTypes'
import type { Geometry } from 'ol/geom'
import { fromLonLat } from 'ol/proj'

/** The codes of the stations inside an area drawn on the map, in the map's projection: a
 * freehand outline, a box or a circle. */
export const stationsInArea = (stations: GeoJsonStation[], area: Geometry): number[] =>
  stations
    .filter(({ geometry }) => area.intersectsCoordinate(fromLonLat(geometry.coordinates)))
    .map(({ properties }) => properties.code)

/** The stations chosen after a click on one: just it, or with Shift it is added or removed. */
export const clickStation = (chosen: number[], code: number, additive: boolean): number[] => {
  if (!additive) {
    return [code]
  }
  return chosen.includes(code) ? chosen.filter(each => each !== code) : [...chosen, code]
}

/** How to name stations chosen on the map, for the chart's title. */
export const areaLabel = (count: number): string =>
  count === 1 ? '1 station in the drawn area' : `${count} stations in the drawn area`
