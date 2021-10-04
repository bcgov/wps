import { StationDaily } from 'api/hfiCalculatorAPI'
import { groupBy } from 'lodash'

export const buildDailyMap = (dailies: StationDaily[]) => {
  const dailiesMap = new Map<number, StationDaily>()

  if (dailies !== undefined) {
    dailies.forEach(daily => {
      dailiesMap.set(daily.code, daily)
    })
  }

  return dailiesMap
}

export const buildWeekliesByCode = (dailies: StationDaily[]) => {
  const weekliesMap = new Map<number, StationDaily[]>()

  if (dailies !== undefined) {
    const weeklies = groupBy(dailies, 'code')
    for (let i = 0; i < Object.keys(weeklies).length; i++) {
      weekliesMap.set(Number(Object.keys(weeklies)[i]), Object.values(weeklies)[i])
    }
  }

  return weekliesMap
}

export const buildWeekliesByDate = (dailies: StationDaily[]) => {
  const weekliesMapDates = new Map<Date, StationDaily[]>()
  if (dailies !== undefined) {
    const weeklies = groupBy(dailies, 'date')
    for (let i = 0; i < Object.keys(weeklies).length; i++) {
      if (weeklies) {
        console.log(weeklies)
        const nextDate = new Date(Object.keys(weeklies)[i])
        const nextValues = Object.values(weeklies)[i]
        weekliesMapDates.set(nextDate, nextValues)
      }
    }
  }
  return weekliesMapDates
}

export const buildWeeklyDates = (weekliesMap: Map<number, StationDaily[]>) => {
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
