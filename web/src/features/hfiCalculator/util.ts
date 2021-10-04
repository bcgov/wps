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

export const buildWeekliesByDate = (
  dailies: StationDaily[]
): Map<Date, StationDaily[]> => {
  const weekliesByDate = new Map<Date, StationDaily[]>()
  const weeklies = groupBy(dailies, (daily: StationDaily) => daily.date)

  if (dailies !== undefined) {
    for (let i = 0; i < Object.keys(weeklies).length; i++) {
      if (weeklies) {
        console.log(weeklies)
        const nextDate = new Date(Object.keys(weeklies)[i])
        const nextValues = Object.values(weeklies)[i]
        weekliesByDate.set(nextDate, nextValues)
      }
    }
  }
  return weekliesByDate
}

/**
 * Return a set of unique dates based on UTC timestamps
 * @param weekliesMap Map of station code -> list of dailies
 * @returns
 */
export const buildWeeklyDates = (
  weekliesMap: Map<number, StationDaily[]>
): Set<number> => {
  const datesList: number[] = []

  weekliesMap.forEach(value => {
    for (let i = 0; i < value.length; i++) {
      if (!datesList.includes(value[i].date.toUTC().toMillis())) {
        datesList.push(value[i].date.toUTC().toMillis())
      }
    }
  })

  const dates = new Set(datesList)
  return dates
}
