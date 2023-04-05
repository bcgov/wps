import { DateTime } from 'luxon'
import { ModelChoice, ObservedDaily } from 'api/moreCast2API'
import {
  defaultsForMissingDailies,
  extendDailiesForStations,
  fillInTheYesterdayDailyBlanks,
  parseYesterdayDailiesForStationsHelper,
  replaceColumnValuesFromYesterdayDaily
} from 'features/moreCast2/yesterdayDailies'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'
import { rowIDHasher } from 'features/moreCast2/util'
import { ColYesterdayDailies } from 'features/moreCast2/slices/columnYesterdaySlice'
import { StationGroupMember } from 'api/stationAPI'
import { omit } from 'lodash'

const START_DATE = '2023-02-16T20:00:00+00:00'
const END_DATE = '2023-02-17T20:00:00+00:00'

const yesterdayDailies: ObservedDaily[] = [
  {
    id: '1',
    data_type: 'YESTERDAY',
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

const stations: StationGroupMember[] = [
  {
    id: '1',
    fire_centre: { id: '1', display_label: 'test' },
    fire_zone: { id: '1', display_label: 'test', fire_centre: 'test' },
    station_status: 'ACTIVE',
    station_code: 1,
    display_label: 'one'
  },
  {
    id: '2',
    fire_centre: { id: '1', display_label: 'test' },
    fire_zone: { id: '1', display_label: 'test', fire_centre: 'test' },
    station_status: 'ACTIVE',
    station_code: 2,
    display_label: 'two'
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
    it('extends the dailies for a date range using the latest daily for a given station', () => {
      const startDate = START_DATE
      const midDate = END_DATE
      const endDate = '2023-02-18T20:00:00+00:00'

      const multipleObservations: ObservedDaily[] = [
        {
          id: '1',
          data_type: 'YESTERDAY',
          station_code: 1,
          station_name: 'test',
          utcTimestamp: startDate,
          temperature: 1,
          relative_humidity: 1,
          precipitation: 1,
          wind_direction: 1,
          wind_speed: 1
        },
        {
          id: '2',
          data_type: 'YESTERDAY',
          station_code: 1,
          station_name: 'test',
          utcTimestamp: midDate,
          temperature: 2,
          relative_humidity: 2,
          precipitation: 2,
          wind_direction: 2,
          wind_speed: 2
        }
      ]
      const result = extendDailiesForStations(multipleObservations, [
        DateTime.fromISO(startDate),
        DateTime.fromISO(endDate)
      ])

      expect(result.length).toEqual(3)

      expect(result[0]).toEqual(multipleObservations[0])
      expect(result[1]).toEqual(multipleObservations[1])
      expect(omit(result[2], ['id', 'utcTimestamp'])).toEqual(omit(multipleObservations[1], ['id', 'utcTimestamp']))
      expect(DateTime.fromISO(result[2].utcTimestamp)).toEqual(DateTime.fromISO(endDate))
    })
  })

  describe('defaultsForMissingDailies', () => {
    it('fills in default dailies for stations without dailies', () => {
      const result = defaultsForMissingDailies(stations, yesterdayDailies, [START_DATE, END_DATE])
      expect(yesterdayDailies).toHaveLength(1)
      expect(result).toHaveLength(2)
      expect(result[0].station_code).toBe(stations[1].station_code)
      expect(result[0].utcTimestamp).toBe('2023-02-16T20:00:00+00:00')
      expect(result[1].station_code).toBe(stations[1].station_code)
      expect(result[1].utcTimestamp).toBe('2023-02-17T20:00:00+00:00')
    })
  })
  describe('fillInTheYesterdayDailyBlanks', () => {
    it('fills in the extended and missing dailies for each station', () => {
      const result = fillInTheYesterdayDailyBlanks(stations, yesterdayDailies, [START_DATE, END_DATE])
      expect(yesterdayDailies).toHaveLength(1)
      expect(result).toHaveLength(4)
      expect(result[0].station_code).toBe(stations[0].station_code)
      expect(DateTime.fromISO(result[0].utcTimestamp)).toEqual(DateTime.fromISO('2023-02-16T20:00:00+00:00'))
      expect(result[1].station_code).toBe(stations[0].station_code)
      expect(DateTime.fromISO(result[1].utcTimestamp)).toEqual(DateTime.fromISO('2023-02-17T20:00:00+00:00'))

      expect(result[2].station_code).toBe(stations[1].station_code)
      expect(DateTime.fromISO(result[2].utcTimestamp)).toEqual(DateTime.fromISO('2023-02-16T20:00:00+00:00'))
      expect(result[3].station_code).toBe(stations[1].station_code)
      expect(DateTime.fromISO(result[3].utcTimestamp)).toEqual(DateTime.fromISO('2023-02-17T20:00:00+00:00'))
    })
  })
  describe('replaceColumnValuesFromPrediction', () => {
    it('should replace the correct row', () => {
      const existingRows: MoreCast2ForecastRow[] = [
        {
          id: rowIDHasher(1, DateTime.fromISO(START_DATE)),
          stationCode: 1,
          stationName: 'one',
          forDate: DateTime.fromISO(START_DATE),
          temp: { value: 1, choice: ModelChoice.GDPS },
          rh: { value: 1, choice: ModelChoice.GDPS },
          precip: { value: 1, choice: ModelChoice.GDPS },
          windSpeed: { value: 1, choice: ModelChoice.GDPS },
          windDirection: { value: 1, choice: ModelChoice.GDPS }
        },
        {
          id: rowIDHasher(2, DateTime.fromISO(END_DATE)),
          stationCode: 2,
          stationName: 'two',
          forDate: DateTime.fromISO(END_DATE),
          temp: { value: 1, choice: ModelChoice.GDPS },
          rh: { value: 1, choice: ModelChoice.GDPS },
          precip: { value: 1, choice: ModelChoice.GDPS },
          windSpeed: { value: 1, choice: ModelChoice.GDPS },
          windDirection: { value: 1, choice: ModelChoice.GDPS }
        }
      ]

      const colPrediction: ColYesterdayDailies = {
        colField: 'temp',
        modelType: 'YESTERDAY',
        yesterdayDailies: [
          {
            id: rowIDHasher(1, DateTime.fromISO(START_DATE)),
            data_type: 'YESTERDAY',
            utcTimestamp: START_DATE,
            precipitation: 2,
            relative_humidity: 2,
            station_code: 1,
            station_name: 'one',
            temperature: 2,
            wind_direction: 2,
            wind_speed: 2
          },
          {
            id: rowIDHasher(2, DateTime.fromISO(END_DATE)),
            data_type: 'YESTERDAY',
            utcTimestamp: END_DATE,
            precipitation: 2,
            relative_humidity: 2,
            station_code: 2,
            station_name: 'two',
            temperature: 2,
            wind_direction: 2,
            wind_speed: 2
          }
        ]
      }
      const result = replaceColumnValuesFromYesterdayDaily(
        existingRows,
        [
          {
            id: '1',
            fire_centre: { id: '1', display_label: 'test' },
            fire_zone: { id: '1', display_label: 'test', fire_centre: 'test' },
            station_status: 'ACTIVE',
            station_code: 1,
            display_label: 'one'
          },
          {
            id: '2',
            fire_centre: { id: '1', display_label: 'test' },
            fire_zone: { id: '1', display_label: 'test', fire_centre: 'test' },
            station_status: 'ACTIVE',
            station_code: 2,
            display_label: 'two'
          }
        ],
        [START_DATE, END_DATE],
        colPrediction
      )
      expect(result).toHaveLength(2)
      expect(result[0].id).toEqual(existingRows[0].id)
      expect(result[0].stationCode).toEqual(existingRows[0].stationCode)
      expect(result[0].stationName).toEqual(existingRows[0].stationName)
      expect(result[0].forDate.toISO()).toEqual(DateTime.fromISO(START_DATE).toISO())
      expect(result[0].temp).toEqual({ value: 2, choice: ModelChoice.YESTERDAY })

      // Other rows remain unchanged
      expect(result[0].rh).toEqual(existingRows[0].rh)
      expect(result[0].precip).toEqual(existingRows[0].precip)
      expect(result[0].windSpeed).toEqual(existingRows[0].windSpeed)
      expect(result[0].windDirection).toEqual(existingRows[0].windDirection)

      expect(result[1].id).toEqual(existingRows[1].id)
      expect(result[1].stationCode).toEqual(existingRows[1].stationCode)
      expect(result[1].stationName).toEqual(existingRows[1].stationName)
      expect(result[1].forDate).toEqual(DateTime.fromISO(END_DATE))
      expect(result[1].temp).toEqual({ value: 2, choice: ModelChoice.YESTERDAY })

      // Other rows remain unchanged
      expect(result[1].rh).toEqual(existingRows[1].rh)
      expect(result[1].precip).toEqual(existingRows[1].precip)
      expect(result[1].windSpeed).toEqual(existingRows[1].windSpeed)
      expect(result[1].windDirection).toEqual(existingRows[1].windDirection)
    })
  })
})
