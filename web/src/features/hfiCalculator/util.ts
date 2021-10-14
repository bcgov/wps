import { WeatherStation, PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { groupBy, isUndefined } from 'lodash'

export const buildDailyMap = (dailies: StationDaily[]): Map<number, StationDaily> => {
  const dailiesMap = new Map<number, StationDaily>()

  if (dailies !== undefined) {
    dailies.forEach(daily => {
      dailiesMap.set(daily.code, daily)
    })
  }

  return dailiesMap
}

export const buildWeekliesByCode = (
  dailies: StationDaily[]
): Map<number, StationDaily[]> => {
  const stationCodeDict = groupBy(dailies, 'code')
  const weekliesMap = new Map<number, StationDaily[]>()

  Object.keys(stationCodeDict).forEach(key => {
    weekliesMap.set(Number(key), stationCodeDict[key])
  })

  return weekliesMap
}

export const buildWeekliesByUTC = (
  dailies: StationDaily[]
): Map<number, StationDaily[]> => {
  const weekliesByUTC = new Map<number, StationDaily[]>()
  const utcDict = groupBy(dailies, (daily: StationDaily) => daily.date.toUTC().toMillis())

  Object.keys(utcDict).forEach(key => {
    weekliesByUTC.set(Number(key), utcDict[key])
  })

  return weekliesByUTC
}

export interface StationWithDaily {
  station: WeatherStation
  daily: StationDaily | undefined
}

export const getDailiesByDay = (
  area: PlanningArea,
  dailiesMap: Map<number, StationDaily>,
  selectedStations: number[]
): StationWithDaily[] => {
  return Object.entries(area.stations)
    .map(([, station]) => ({
      station,
      daily: dailiesMap.get(station.code)
    }))
    .filter(record => selectedStations.includes(record.station.code))
}

export const getDailiesByWeekDay = (
  area: PlanningArea,
  dayTimestamp: number,
  weekliesByUTC: Map<number, StationDaily[]>,
  selectedStations: number[]
): StationWithDaily[] => {
  const dailiesForDay = weekliesByUTC.get(dayTimestamp)
  if (isUndefined(dailiesForDay)) {
    return []
  }
  const dailiesByCode = new Map(dailiesForDay.map(daily => [daily.code, daily]))
  return getDailiesByDay(area, dailiesByCode, selectedStations)
}
