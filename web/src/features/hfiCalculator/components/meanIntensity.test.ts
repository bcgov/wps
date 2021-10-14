import {
  calculateMeanIntensityGroup,
  getDailiesByDay,
  StationWithDaily
} from 'features/hfiCalculator/components/meanIntensity'
import { WeatherStation, PlanningArea } from 'api/hfiCalcAPI'
import { StationDaily } from 'api/hfiCalculatorAPI'
import {
  buildStation,
  buildStationDaily
} from 'features/hfiCalculator/components/testHelpers'

const buildStationWithDaily = (
  station: WeatherStation,
  stationDaily: StationDaily
): StationWithDaily => {
  return { station: station, daily: stationDaily }
}

describe('calculateMeanIntensityGroup', () => {
  it('should return the average of all intensity groups within the list of StationDailies', () => {
    const stationWithDailies: StationWithDaily[] = [
      buildStationWithDaily(buildStation(1), buildStationDaily(1, 2)),
      buildStationWithDaily(buildStation(2), buildStationDaily(2, 4))
    ]
    expect(calculateMeanIntensityGroup(stationWithDailies, [1, 2])).toEqual(3)
  })
  it('should return undefined if there are no intensity groups to calculate in the selected dailies', () => {
    const stationWithDailies: StationWithDaily[] = [
      buildStationWithDaily(buildStation(1), buildStationDaily(1, 2)),
      buildStationWithDaily(buildStation(2), buildStationDaily(2, 4))
    ]
    expect(calculateMeanIntensityGroup(stationWithDailies, [0])).toEqual(undefined)
  })
})

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
