import { DateTime } from 'luxon'
import { ModelChoice, YesterdayDaily } from 'api/moreCast2API'
import {
  defaultsForMissingDailies,
  extendDailiesForStations,
  fillInTheYesterdayDailyBlanks,
  parseYesterdayDailiesForStationsHelper
} from 'features/moreCast2/yesterdayDailies'
import { FireCenterStation } from 'api/fbaAPI'

const START_DATE = '2023-02-16T20:00:00+00:00'
const END_DATE = '2023-02-17T20:00:00+00:00'

const yesterdayDailies: YesterdayDaily[] = [
  {
    id: '1',
    station_code: 1,
    station_name: 'test',
    utcTimestamp: START_DATE,
    temperature: 1,
    relative_humidity: 1,
    precipitation: 1,
    wind_direction: 1,
    wind_speed: 1
  }
]

const stations: FireCenterStation[] = [
  {
    code: 1,
    name: 'one'
  },
  {
    code: 2,
    name: 'two'
  }
]

describe('yesterdayDailies', () => {
  describe('parseYesterdayDailiesForStationsHelper', () => {
    it('should return morecast2forecastrow for a station daily', () => {
      const result = parseYesterdayDailiesForStationsHelper(yesterdayDailies)
      expect(result.length).toEqual(1)
      expect(result[0].id).toEqual(yesterdayDailies[0].id)
      expect(result[0].stationCode).toEqual(yesterdayDailies[0].station_code)
      expect(result[0].stationName).toEqual(yesterdayDailies[0].station_name)
      expect(result[0].forDate).toEqual(DateTime.fromISO(yesterdayDailies[0].utcTimestamp))
      expect(result[0].temp.choice).toEqual(ModelChoice.YESTERDAY)
      expect(result[0].temp.value).toEqual(yesterdayDailies[0].temperature)
      expect(result[0].precip.choice).toEqual(ModelChoice.YESTERDAY)
      expect(result[0].precip.value).toEqual(yesterdayDailies[0].precipitation)
      expect(result[0].windDirection.choice).toEqual(ModelChoice.YESTERDAY)
      expect(result[0].windDirection.value).toEqual(yesterdayDailies[0].wind_direction)
      expect(result[0].windSpeed.choice).toEqual(ModelChoice.YESTERDAY)
      expect(result[0].windSpeed.value).toEqual(yesterdayDailies[0].wind_speed)
    })
  })
  describe('extendDailiesForStations', () => {
    it('extends the dailies for a date range', () => {
      const result = extendDailiesForStations(yesterdayDailies, [
        DateTime.fromISO(START_DATE),
        DateTime.fromISO(END_DATE)
      ])

      expect(result.length).toEqual(2)

      expect(DateTime.fromISO(result[0].utcTimestamp)).toEqual(DateTime.fromISO(START_DATE))
      expect(DateTime.fromISO(result[1].utcTimestamp)).toEqual(DateTime.fromISO(END_DATE))
    })
  })

  describe('defaultsForMissingDailies', () => {
    it('fills in default dailies for stations without dailies', () => {
      const result = defaultsForMissingDailies(stations, yesterdayDailies, [START_DATE, END_DATE])
      expect(yesterdayDailies).toHaveLength(1)
      expect(result).toHaveLength(2)
      expect(result[0].station_code).toBe(stations[1].code)
      expect(result[0].utcTimestamp).toBe('2023-02-16T20:00:00+00:00')
      expect(result[1].station_code).toBe(stations[1].code)
      expect(result[1].utcTimestamp).toBe('2023-02-17T20:00:00+00:00')
    })
  })
  describe('fillInTheYesterdayDailyBlanks', () => {
    it('fills in the extended and missing dailies for each station', () => {
      const result = fillInTheYesterdayDailyBlanks(stations, yesterdayDailies, [START_DATE, END_DATE])
      expect(yesterdayDailies).toHaveLength(1)
      expect(result).toHaveLength(4)
      expect(result[0].station_code).toBe(stations[0].code)
      expect(DateTime.fromISO(result[0].utcTimestamp)).toEqual(DateTime.fromISO('2023-02-16T20:00:00+00:00'))
      expect(result[1].station_code).toBe(stations[0].code)
      expect(DateTime.fromISO(result[1].utcTimestamp)).toEqual(DateTime.fromISO('2023-02-17T20:00:00+00:00'))

      expect(result[2].station_code).toBe(stations[1].code)
      expect(DateTime.fromISO(result[2].utcTimestamp)).toEqual(DateTime.fromISO('2023-02-16T20:00:00+00:00'))
      expect(result[3].station_code).toBe(stations[1].code)
      expect(DateTime.fromISO(result[3].utcTimestamp)).toEqual(DateTime.fromISO('2023-02-17T20:00:00+00:00'))
    })
  })
})
