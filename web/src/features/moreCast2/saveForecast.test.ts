import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { getRowsToSave, isForecastValid, validForecastPredicate } from 'features/moreCast2/saveForecasts'
import { DateTime } from 'luxon'

const baseRow = {
  precipActual: 0,
  precipGDPS: 0,
  precipGFS: 0,
  precipHRDPS: 0,
  precipRDPS: 0,
  rhActual: 0,
  rhGDPS: 0,
  rhGFS: 0,
  rhHRDPS: 0,
  rhRDPS: 0,
  tempActual: 0,
  tempGDPS: 0,
  tempGFS: 0,
  tempHRDPS: 0,
  tempRDPS: 0,
  windDirectionActual: 0,
  windDirectionGDPS: 0,
  windDirectionGFS: 0,
  windDirectionHRDPS: 0,
  windDirectionRDPS: 0,
  windSpeedActual: 0,
  windSpeedGDPS: 0,
  windSpeedGFS: 0,
  windSpeedHRDPS: 0,
  windSpeedRDPS: 0
}

const mockForDate = DateTime.fromISO('2023-02-16T20:00:00+00:00')

const buildValidForecast = (id: string, forDate: DateTime, stationCode: number, stationName: string): MoreCast2Row => ({
  id,
  forDate,
  stationCode,
  stationName,
  ...baseRow,
  precipForecast: { choice: 'GDPS', value: 0 },
  rhForecast: { choice: 'GDPS', value: 0 },
  tempForecast: { choice: 'GDPS', value: 0 },
  windDirectionForecast: { choice: 'GDPS', value: 0 },
  windSpeedForecast: { choice: 'GDPS', value: 0 }
})

const buildInvalidForecast = (
  id: string,
  forDate: DateTime,
  stationCode: number,
  stationName: string
): MoreCast2Row => ({
  id,
  forDate,
  stationCode,
  stationName,
  ...baseRow
})

const buildNAForecast = (id: string, forDate: DateTime, stationCode: number, stationName: string): MoreCast2Row => ({
  id,
  forDate,
  stationCode,
  stationName,
  ...baseRow,
  precipForecast: { choice: '', value: NaN },
  rhForecast: { choice: '', value: NaN },
  tempForecast: { choice: '', value: NaN },
  windDirectionForecast: { choice: '', value: NaN },
  windSpeedForecast: { choice: '', value: NaN }
})

describe.only('saveForecasts', () => {
  describe('isForecastValid', () => {
    it('should return true if all forecasts fields are set', () => {
      expect(
        isForecastValid([
          buildValidForecast('1', mockForDate, 1, 'one'),
          buildValidForecast('2', mockForDate, 2, 'two')
        ])
      ).toBe(true)
    })

    it('should return false if any forecasts have missing forecast fields set', () => {
      expect(
        isForecastValid([
          buildValidForecast('1', mockForDate, 1, 'one'),
          buildInvalidForecast('2', mockForDate, 2, 'two')
        ])
      ).toBe(false)
    })

    it('should return false if any forecasts have missing forecast fields set', () => {
      expect(
        isForecastValid([buildValidForecast('1', mockForDate, 1, 'one'), buildNAForecast('2', mockForDate, 2, 'two')])
      ).toBe(false)
    })
  })
  describe('validForecastPredicate', () => {
    it('should return false for a forecast with missing forecast fields', () => {
      expect(validForecastPredicate(buildInvalidForecast('1', mockForDate, 1, 'one'))).toBe(false)
    })
    it('should return false for a forecast with forecasts but N/A values', () => {
      expect(validForecastPredicate(buildNAForecast('1', mockForDate, 1, 'one'))).toBe(false)
    })
  })
  describe('getRowsToSave', () => {
    it('should filter out invalid forecasts', () => {
      const res = getRowsToSave([
        buildValidForecast('1', mockForDate, 1, 'one'),
        buildInvalidForecast('2', mockForDate, 2, 'two')
      ])
      expect(res).toHaveLength(1)
      expect(res[0].id).toBe('1')
    })
    it('should filter out N/A forecasts', () => {
      const res = getRowsToSave([
        buildValidForecast('1', mockForDate, 1, 'one'),
        buildNAForecast('2', mockForDate, 2, 'two')
      ])
      expect(res).toHaveLength(1)
      expect(res[0].id).toBe('1')
    })
  })
})
