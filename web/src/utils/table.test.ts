import { WeatherValue } from 'features/fireWeather/components/tables/SortableTableByDatetime'
import {
  getDatetimeComparator,
  getMinMaxValueCalculator,
  getMinMaxValuesRowIds,
  MinMaxValues
} from 'utils/table'

const dummyWeatherData: WeatherValue[] = [
  {
    datetime: '2020-12-09T20:00:00+00:00',
    temperature: 8.1,
    relative_humidity: 70,
    wind_direction: 300,
    wind_speed: 17.3,
    precipitation: 0.4
  },
  {
    datetime: '2020-12-09T19:00:00+00:00',
    temperature: 10.5,
    relative_humidity: 53,
    wind_direction: 260,
    wind_speed: 3.7,
    precipitation: 0.8
  },
  {
    datetime: '2020-12-09T18:00:00+00:00',
    temperature: -1.5,
    relative_humidity: 28,
    wind_direction: 330,
    wind_speed: 63.2,
    precipitation: 0.0
  },
  {
    datetime: '2020-12-09T17:00:00+00:00',
    temperature: 2.4,
    relative_humidity: 35,
    wind_direction: 150,
    wind_speed: 4.7,
    precipitation: 16.3
  },
  {
    datetime: '2020-12-09T16:00:00+00:00',
    temperature: -1.5,
    relative_humidity: 25,
    wind_direction: 280,
    wind_speed: 2.5,
    precipitation: 0.0
  }
]

const correctMinMaxValues: MinMaxValues = {
  relative_humidity: 25,
  precipitation: 16.3,
  wind_speed: 63.2,
  temperature: {
    min: -1.5,
    max: 10.5
  }
}

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
  })

  describe('getMinMaxValuesRowIds', () => {
    it('should correctly determine the rows ids of min-max values to be highlighted', () => {
      const minMaxRowIds = getMinMaxValuesRowIds(dummyWeatherData, correctMinMaxValues)

      expect(minMaxRowIds).toEqual({
        relative_humidity: [4],
        precipitation: [3],
        wind: [2],
        max_temp: [1],
        min_temp: [2, 4]
      })
    })
  })
})
