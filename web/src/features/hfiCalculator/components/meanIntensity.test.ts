import { calculateMeanIntensityGroup } from 'features/hfiCalculator/components/meanIntensity'
import {
  buildStation,
  buildStationDaily,
  buildStationWithDaily
} from 'features/hfiCalculator/components/testHelpers'
import { StationWithDaily } from 'features/hfiCalculator/util'

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
