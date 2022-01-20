import { PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { chain, groupBy, sortBy, take } from 'lodash'
import { DateTime } from 'luxon'

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

export const getDailiesForCSV = (
  numPrepDays: number,
  dailies: StationDaily[]
): StationDaily[] => {
  // Group all dailies by their station code, then take only the number we need for each station
  return chain(dailies)
    .groupBy(daily => daily.code)
    .map((stationDailies, code) => ({ code, stationDailies }))
    .value()
    .map(({ stationDailies }) => take(stationDailies, numPrepDays))
    .flat()
}

export const getDailiesByStationCode = (
  numPrepDays: number,
  selectedPrepDayIso: string | null,
  dailies: StationDaily[],
  stationCode: number
): StationDaily[] => {
  const selectedPrepDayDate = selectedPrepDayIso
    ? DateTime.fromISO(selectedPrepDayIso)
    : undefined
  const stationCodeDict = groupBy(dailies, 'code')
  const dailiesByCode = new Map<number, StationDaily[]>()

  Object.keys(stationCodeDict).forEach(key => {
    dailiesByCode.set(Number(key), stationCodeDict[key])
  })

  const dailiesForCode = take(
    sortBy(dailiesByCode.get(stationCode), daily => daily.date.toMillis()),
    numPrepDays
  )

  return dailiesForCode ? dailiesForCode : []
}
