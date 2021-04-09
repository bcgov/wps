import { Station } from '/Users/conor/projects/wps/web/src/api/stationAPI'

export interface Option {
  name: string
  code: number
}

export const getAutoCompleteOption = (
  stationCodes: number[],
  stationsByCode: Record<number, Station | undefined>
): { isThereUnknownCode: boolean; autocompleteValue: Option[] } => {
  let isThereUnknownCode = false
  const autocompleteValue: Option[] = stationCodes.map(code => {
    const station = stationsByCode[code]
    if (station) {
      return { name: station.properties.name, code: station.properties.code }
    }

    isThereUnknownCode = true
    return { name: 'Unknown', code }
  })
  return { isThereUnknownCode, autocompleteValue }
}
