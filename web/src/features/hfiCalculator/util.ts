import { StationDaily } from 'api/hfiCalculatorAPI'
import { groupBy } from 'lodash'

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
