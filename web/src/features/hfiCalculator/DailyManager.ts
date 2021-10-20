import { PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { groupBy } from 'lodash'

/**
 * Accepts a list of station dailies and exposes
 * public methods to access those dailies with different shapes.
 */
export class DailyManager {
  constructor(private readonly dailies: StationDaily[], selected: number[]) {}

  public getDailiesByStationCode = (): Map<number, StationDaily[]> => {
    const stationCodeDict = groupBy(this.dailies, 'code')
    const weekliesMap = new Map<number, StationDaily[]>()

    Object.keys(stationCodeDict).forEach(key => {
      weekliesMap.set(Number(key), stationCodeDict[key])
    })

    return weekliesMap
  }
  public getDailiesByDayUTC = (): Map<number, StationDaily[]> => {
    const dailiesByDayUTC = new Map<number, StationDaily[]>()
    const utcDict = groupBy(this.dailies, (daily: StationDaily) =>
      daily.date.toUTC().toMillis()
    )

    Object.keys(utcDict).forEach(key => {
      dailiesByDayUTC.set(Number(key), utcDict[key])
    })

    return dailiesByDayUTC
  }

  public getDailiesForArea = (area: PlanningArea) => {
    const areaStationCodes = new Set(
      Object.entries(area.stations).map(([, station]) => station.code)
    )
    return this.dailies.filter(daily => areaStationCodes.has(daily.code))
  }

  public lookupDailiesByTimestamp = (utcTimestamp: number): StationDaily[] => {
    const dailies = this.getDailiesByDayUTC().get(utcTimestamp)

    return dailies ? dailies : []
  }

  public lookupDailiesByStationCode = (stationCode: number): StationDaily[] => {
    const dailies = this.getDailiesByStationCode().get(stationCode)

    return dailies ? dailies : []
  }

  public static asStationsWithDaily = (area: PlanningArea, dailies: StationDaily[]) => {
    const dailiesMap = new Map(dailies.map(daily => [daily.code, daily]))
    return Object.entries(area.stations).map(([, station]) => ({
      station,
      daily: dailiesMap.get(station.code)
    }))
  }
}
