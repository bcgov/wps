import { StationDaily } from 'api/hfiCalculatorAPI'
// import {
//   calculateMeanIntensity,
//   calculateMeanIntensityGroupLevel
// } from 'features/hfiCalculator/components/meanIntensity'
import { buildStationDaily } from 'features/hfiCalculator/components/testHelpers'

describe('calculateMeanIntensityGroup', () => {
  xit('should return the average of all intensity groups within the list of StationDailies', () => {
    const stationDailies: StationDaily[] = [
      buildStationDaily(1, 2),
      buildStationDaily(2, 4)
    ]
    // expect(calculateMeanIntensity(stationDailies)).toEqual(3)
  })
  xit('should return undefined if there are no intensity groups to calculate in the selected dailies', () => {
    // expect(calculateMeanIntensity([])).toEqual(undefined)
  })
  xit('should return undefined if there is no mean intensity group to calculate', () => {
    // expect(calculateMeanIntensityGroupLevel([])).toEqual(undefined)
  })
})
