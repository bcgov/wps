import { DetailedGeoJsonStation, GeoJsonStation } from 'api/stationAPI'

export interface Option {
  name: string
  code: number
}

/**
 * Returns the selected stations as options based on the selectedStationCodes.
 *
 * If stationsByCode map does not contain any of the selected codes a default unknown
 * option is added.
 */
export const getSelectedStationOptions = (
  selectedStationCodes: number[],
  stationsByCode: Record<number, GeoJsonStation | DetailedGeoJsonStation | undefined>
): { isThereUnknownCode: boolean; selectedStationOptions: Option[] } => {
  let isThereUnknownCode = false
  const selectedStationOptions: Option[] = selectedStationCodes.map(code => {
    const station = stationsByCode[code]
    if (station) {
      return { name: station.properties.name, code: station.properties.code }
    }

    isThereUnknownCode = true
    return { name: 'Unknown', code }
  })
  return { isThereUnknownCode, selectedStationOptions }
}
