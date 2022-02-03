import { PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { ValidatedStationDaily } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { groupBy, sortBy, take } from 'lodash'

export const getDailiesForArea = (
  area: PlanningArea,
  dailies: StationDaily[],
  selected: number[]
): StationDaily[] => {
  const areaStationCodes = new Set(
    Object.entries(area.stations).map(([, station]) => station.code)
  )
  return dailies.filter(
    daily => selected.includes(daily.code) && areaStationCodes.has(daily.code)
  )
}

export const getZoneFromAreaName = (areaName: string): string => {
  return areaName.slice(-3)
}

export const getDailiesByStationCode = (
  numPrepDays: number,
  dailies: ValidatedStationDaily[],
  stationCode: number
): ValidatedStationDaily[] => {
  const stationCodeDict = groupBy(dailies, 'code')
  const dailiesByCode = new Map<number, ValidatedStationDaily[]>()

  Object.keys(stationCodeDict).forEach(key => {
    dailiesByCode.set(Number(key), stationCodeDict[key])
  })

  const dailiesForCode = take(
    sortBy(dailiesByCode.get(stationCode), daily => daily.date.toMillis()),
    numPrepDays
  )

  return dailiesForCode ? dailiesForCode : []
}
