import { StationDaily } from 'api/hfiCalculatorAPI'
import {
  calculateDailyMeanIntensities,
  calculateMeanIntensity,
  calculatePrepLevel,
  FIRE_STARTS_SET,
  highestFireStarts,
  lowestFireStarts,
  one2TwoStarts,
  three2SixStarts,
  two2ThreeStarts
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { buildStationDaily } from 'features/hfiCalculator/components/testHelpers'
describe('hfiCalculatorSlice', () => {
  describe('calculateMeanIntensity', () => {
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
  describe('prepLevel', () => {
    it('should return undefined for prep level when mig is undefined', () => {
      FIRE_STARTS_SET.forEach(fireStarts => {
        expect(calculatePrepLevel(undefined, fireStarts)).toBe(undefined)
      })
    })
    it('should return least severe prep levels for lowest fire starts range', () => {
      expect(calculatePrepLevel(1, lowestFireStarts)).toBe(1)
      expect(calculatePrepLevel(2, lowestFireStarts)).toBe(1)
      expect(calculatePrepLevel(3, lowestFireStarts)).toBe(2)
      expect(calculatePrepLevel(4, lowestFireStarts)).toBe(3)
      expect(calculatePrepLevel(5, lowestFireStarts)).toBe(4)
    })
    it('should return 1:1 prep levels for 1-2 fire starts range', () => {
      expect(calculatePrepLevel(1, one2TwoStarts)).toBe(1)
      expect(calculatePrepLevel(2, one2TwoStarts)).toBe(2)
      expect(calculatePrepLevel(3, one2TwoStarts)).toBe(3)
      expect(calculatePrepLevel(4, one2TwoStarts)).toBe(4)
      expect(calculatePrepLevel(5, one2TwoStarts)).toBe(5)
    })
    it('should return prep levels from 2 to 6 for 2-3 fire starts range', () => {
      expect(calculatePrepLevel(1, two2ThreeStarts)).toBe(2)
      expect(calculatePrepLevel(2, two2ThreeStarts)).toBe(3)
      expect(calculatePrepLevel(3, two2ThreeStarts)).toBe(4)
      expect(calculatePrepLevel(4, two2ThreeStarts)).toBe(5)
      expect(calculatePrepLevel(5, two2ThreeStarts)).toBe(6)
    })
    it('should return prep levels from 3 to 6 for 3-6 fire starts range', () => {
      expect(calculatePrepLevel(1, three2SixStarts)).toBe(3)
      expect(calculatePrepLevel(2, three2SixStarts)).toBe(4)
      expect(calculatePrepLevel(3, three2SixStarts)).toBe(5)
      expect(calculatePrepLevel(4, three2SixStarts)).toBe(6)
      expect(calculatePrepLevel(5, three2SixStarts)).toBe(6)
    })
    it('should return prep levels from 4 to 6 for 6+ fire starts range', () => {
      expect(calculatePrepLevel(1, highestFireStarts)).toBe(4)
      expect(calculatePrepLevel(2, highestFireStarts)).toBe(5)
      expect(calculatePrepLevel(3, highestFireStarts)).toBe(6)
      expect(calculatePrepLevel(4, highestFireStarts)).toBe(6)
      expect(calculatePrepLevel(5, highestFireStarts)).toBe(6)
    })
  })
})
