import { PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { groupBy } from 'lodash'
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

export const getDailiesForDate = (
  dailies: StationDaily[],
  dateOfInterest: DateTime
): StationDaily[] => {
  return dailies.filter(
    daily => daily.date.toFormat('MM-dd-yyyy') == dateOfInterest.toFormat('MM-dd-yyyy')
  )
}

export const getDailiesByStationCode = (
  dailies: StationDaily[],
  stationCode: number
): StationDaily[] => {
  const stationCodeDict = groupBy(dailies, 'code')
  const dailiesByCode = new Map<number, StationDaily[]>()

  Object.keys(stationCodeDict).forEach(key => {
    dailiesByCode.set(Number(key), stationCodeDict[key])
  })

  const dailiesForCode = dailiesByCode.get(stationCode)

  return dailiesForCode ? dailiesForCode : []
}
