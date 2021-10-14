import { WeatherStation, PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import {
  buildStation,
  buildStationDaily,
  buildStationWithDaily
} from 'features/hfiCalculator/components/testHelpers'
import { getDailiesByDay } from 'features/hfiCalculator/util'

describe('getDailiesByDay', () => {
  it('should return a map of dailies on the given day sorted by station code', () => {
    const stations: Record<number, WeatherStation> = {
      1: buildStation(1),
      2: buildStation(2),
      3: buildStation(3)
    }
    const area: PlanningArea = { id: 1, name: 'afton', stations: stations }
    const dailiesMap: Map<number, StationDaily> = new Map()
    dailiesMap.set(2, buildStationDaily(2, 2))
    dailiesMap.set(1, buildStationDaily(1, 1))
    dailiesMap.set(3, buildStationDaily(3, 3))

    const expectedResponse = [
      buildStationWithDaily(buildStation(1), buildStationDaily(1, 1)),
      buildStationWithDaily(buildStation(2), buildStationDaily(2, 2)),
      buildStationWithDaily(buildStation(3), buildStationDaily(3, 3))
    ]
    expect(getDailiesByDay(area, dailiesMap, [1, 2, 3])).toEqual(expectedResponse)
  })
})
