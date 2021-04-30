import {
  getDatetimeComparator,
  getMinMaxValueCalculator,
  getMinMaxValuesRowIds
} from 'utils/table'
import {
  dummyWeatherData,
  dummyWeatherDataNoPrecip,
  dummyWeatherDataNoWind,
  dummyWeatherDataMultiplePrecipLabels,
  dummyWeatherDataNullValues,
  correctMinMaxValues,
  correctMinMaxValuesNoPrecip,
  correctMinMaxValuesNoWind,
  correctMinMaxValuesMultiplePrecipLabels,
  correctMinMaxValuesNullValues,
  correctMinMaxRowIds,
  correctMinMaxRowIdsNoPrecip,
  correctMinMaxRowIdsNoWind
} from 'utils/table.test.data'

describe('Table util functions', () => {
  describe('getDatetimeComparator', () => {
    it('should return the correct compare function', () => {
      const ascending = getDatetimeComparator('asc')
      const descending = getDatetimeComparator('desc')
      const arr = [
        { datetime: '2020-12-09T23:00:00+00:00', meta: 'hmm' },
        { datetime: '2020-12-09T21:00:00+00:00' },
        { datetime: '2020-12-09T20:00:00+00:00' },
        { datetime: '2020-12-09T22:00:00+00:00' }
      ]
      const deepCopy = JSON.parse(JSON.stringify(arr))

      expect([...arr].sort(ascending)).toEqual([
        { datetime: '2020-12-09T20:00:00+00:00' },
        { datetime: '2020-12-09T21:00:00+00:00' },
        { datetime: '2020-12-09T22:00:00+00:00' },
        { datetime: '2020-12-09T23:00:00+00:00', meta: 'hmm' }
      ])

      expect([...arr].sort(descending)).toEqual([
        { datetime: '2020-12-09T23:00:00+00:00', meta: 'hmm' },
        { datetime: '2020-12-09T22:00:00+00:00' },
        { datetime: '2020-12-09T21:00:00+00:00' },
        { datetime: '2020-12-09T20:00:00+00:00' }
      ])

      expect(arr).toEqual(deepCopy)
    })
  })

  describe('getMinMaxValueCalculator', () => {
    it('should correctly calculate min and max wx values to be highlighted', () => {
      const minMaxValues = getMinMaxValueCalculator(dummyWeatherData)

      expect(minMaxValues).toEqual(correctMinMaxValues)
    })

    it('should return null for max precip when all precips are 0.0', () => {
      const minMaxValues = getMinMaxValueCalculator(dummyWeatherDataNoPrecip)
      expect(minMaxValues).toEqual(correctMinMaxValuesNoPrecip)
    })

    it('should return null for max wind_speed when all wind_speeds are 0.0', () => {
      const minMaxValues = getMinMaxValueCalculator(dummyWeatherDataNoWind)
      expect(minMaxValues).toEqual(correctMinMaxValuesNoWind)
    })

    it('should correctly calculate min-max values when different precip labels are used', () => {
      const minMaxValues = getMinMaxValueCalculator(dummyWeatherDataMultiplePrecipLabels)
      expect(minMaxValues).toEqual(correctMinMaxValuesMultiplePrecipLabels)
    })

    it('should calculate min-max wx values when some values are null', () => {
      const minMaxValues = getMinMaxValueCalculator(dummyWeatherDataNullValues)
      expect(minMaxValues).toEqual(correctMinMaxValuesNullValues)
    })
  })

  describe('getMinMaxValuesRowIds', () => {
    it('should correctly determine the rows ids of min-max values to be highlighted', () => {
      const minMaxRowIds = getMinMaxValuesRowIds(dummyWeatherData, correctMinMaxValues)
      expect(minMaxRowIds).toEqual(correctMinMaxRowIds)
    })

    it('should return empty rowIds list when min-max value is null', () => {
      let minMaxRowIds = getMinMaxValuesRowIds(
        dummyWeatherDataNoPrecip,
        correctMinMaxValuesNoPrecip
      )
      expect(minMaxRowIds).toEqual(correctMinMaxRowIdsNoPrecip)

      minMaxRowIds = getMinMaxValuesRowIds(
        dummyWeatherDataNoWind,
        correctMinMaxValuesNoWind
      )
      expect(minMaxRowIds).toEqual(correctMinMaxRowIdsNoWind)
    })
  })
})
