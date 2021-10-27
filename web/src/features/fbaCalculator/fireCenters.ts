import { GeoJsonStation, DetailedGeoJsonStation } from 'api/stationAPI'

const KAMLOOPS_STATIONS = new Set([
  239, 266, 305, 322, 1082, 1108, 280, 306, 309, 1029, 1055, 836, 1399, 328, 334, 286,
  298, 344, 346, 388
])
// Placeholder filter function
export const filterStations = (
  stations: GeoJsonStation[] | DetailedGeoJsonStation[]
): GeoJsonStation[] | DetailedGeoJsonStation[] => {
  return stations.filter(station => KAMLOOPS_STATIONS.has(station.properties.code))
}
