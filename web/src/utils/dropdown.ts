import { Station } from 'api/stationAPI'

export interface Option {
  name: string
  code: number
}

export const getSelectedStationOptions = (
  stationCodes: number[],
  stationsByCode: Record<number, Station | undefined>
): { isThereUnknownCode: boolean; selectedStationOptions: Option[] } => {
  let isThereUnknownCode = false
  const selectedStationOptions: Option[] = stationCodes.map(code => {
    const station = stationsByCode[code]
    if (station) {
      return { name: station.properties.name, code: station.properties.code }
    }

    isThereUnknownCode = true
    return { name: 'Unknown', code }
  })
  return { isThereUnknownCode, selectedStationOptions }
}
