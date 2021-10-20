import { PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { groupBy } from 'lodash'

/**
 * Accepts a list of station dailies and exposes
 * public methods to access those dailies with different shapes.
 */
export class DailyManager {
  constructor(
    private readonly dailies: StationDaily[],
    private readonly selected: number[]
  ) {}

  public getDailiesByStationCode = (): Map<number, StationDaily[]> => {
    const stationCodeDict = groupBy(this.dailies, 'code')
    const weekliesMap = new Map<number, StationDaily[]>()

    Object.keys(stationCodeDict).forEach(key => {
      weekliesMap.set(Number(key), stationCodeDict[key])
    })

    return weekliesMap
  }

  public getDailiesForArea = (area: PlanningArea) => {
    const areaStationCodes = new Set(
      Object.entries(area.stations).map(([, station]) => station.code)
    )
    return this.dailies.filter(daily => areaStationCodes.has(daily.code))
  }

  public lookupDailiesByStationCode = (stationCode: number): StationDaily[] => {
    const dailies = this.getDailiesByStationCode().get(stationCode)

    return dailies ? dailies : []
  }
}
