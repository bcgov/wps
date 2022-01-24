import { StationDaily } from 'api/hfiCalculatorAPI'
import {
  calculateDailyMeanIntensities,
  calculateMeanIntensity
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { buildStationDaily } from 'features/hfiCalculator/components/testHelpers'

describe('calculateMeanIntensity functions', () => {
  it('should return the average of all intensity groups within the list of StationDailies', () => {
    const stationDailies: StationDaily[] = [
      buildStationDaily(1, 2),
      buildStationDaily(2, 4)
    ]
    expect(calculateMeanIntensity(stationDailies)).toEqual(3)
  })
  it('should return undefined if there are no intensity groups to calculate in the selected dailies', () => {
    expect(calculateMeanIntensity([])).toEqual(undefined)
  })
  it('should return undefined if there is no mean intensity group to calculate', () => {
    expect(calculateDailyMeanIntensities([], 1)).toEqual([undefined])
  })
})
