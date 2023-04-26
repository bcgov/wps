import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { getRowsToSave, isForecastValid, validForecastPredicate } from 'features/moreCast2/saveForecasts'
import { DateTime } from 'luxon'

const baseRow = {
  precipActual: NaN,
  precipGDPS: 0,
  precipGFS: 0,
  precipHRDPS: 0,
  precipNAM: 0,
  precipRDPS: 0,
  rhActual: NaN,
  rhGDPS: 0,
  rhGFS: 0,
  rhHRDPS: 0,
  rhNAM: 0,
  rhRDPS: 0,
  tempActual: NaN,
  tempGDPS: 0,
  tempGFS: 0,
  tempHRDPS: 0,
  tempNAM: 0,
  tempRDPS: 0,
  windDirectionActual: NaN,
  windDirectionGDPS: 0,
  windDirectionGFS: 0,
  windDirectionNAM: 0,
  windDirectionHRDPS: 0,
  windDirectionRDPS: 0,
  windSpeedActual: NaN,
  windSpeedGDPS: 0,
  windSpeedGFS: 0,
  windSpeedHRDPS: 0,
  windSpeedNAM: 0,
  windSpeedRDPS: 0
}

const baseRowWithActuals = {
  ...baseRow,
  precipActual: 0,
  rhActual: 0,
  tempActual: 0,
  windDirectionActual: 0,
  windSpeedActual: 0
}

const mockForDate = DateTime.fromISO('2023-02-16T20:00:00+00:00')

const buildCompleteForecast = (
  id: string,
  forDate: DateTime,
  stationCode: number,
  stationName: string
): MoreCast2Row => ({
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

const buildForecastMissingWindDirection = (
  id: string,
  forDate: DateTime,
  stationCode: number,
  stationName: string
): MoreCast2Row => ({
  id,
  forDate,
  stationCode,
  stationName,
  ...baseRow,
  precipForecast: { choice: 'GDPS', value: 0 },
  rhForecast: { choice: 'GDPS', value: 0 },
  tempForecast: { choice: 'GDPS', value: 0 },
  windDirectionForecast: { choice: '', value: NaN },
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

const buildForecastWithActuals = (
  id: string,
  forDate: DateTime,
  stationCode: number,
  stationName: string
): MoreCast2Row => ({
  id,
  forDate,
  stationCode,
  stationName,
  ...baseRowWithActuals,
  precipForecast: { choice: 'GDPS', value: 0 },
  rhForecast: { choice: 'GDPS', value: 0 },
  tempForecast: { choice: 'GDPS', value: 0 },
  windDirectionForecast: { choice: 'GDPS', value: 0 },
  windSpeedForecast: { choice: 'GDPS', value: 0 }
})

describe.only('saveForecasts', () => {
  describe('isForecastValid', () => {
    it('should return true if all forecasts fields are set', () => {
      expect(
        isForecastValid([
          buildCompleteForecast('1', mockForDate, 1, 'one'),
          buildCompleteForecast('2', mockForDate, 2, 'two')
        ])
      ).toBe(true)
    })
    it('should return true if all forecasts fields are set except windDirectionForecast', () => {
      expect(
        isForecastValid([
          buildForecastMissingWindDirection('1', mockForDate, 1, 'one'),
          buildForecastMissingWindDirection('2', mockForDate, 2, 'two')
        ])
      ).toBe(true)
    })

    it('should return false if any forecasts have missing forecast fields', () => {
      expect(
        isForecastValid([
          buildCompleteForecast('1', mockForDate, 1, 'one'),
          buildInvalidForecast('2', mockForDate, 2, 'two')
        ])
      ).toBe(false)
    })

    it('should return false if any forecasts have missing forecast fields set other than windDirectionForecast', () => {
      expect(
        isForecastValid([
          buildCompleteForecast('1', mockForDate, 1, 'one'),
          buildNAForecast('2', mockForDate, 2, 'two')
        ])
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
        buildCompleteForecast('1', mockForDate, 1, 'one'),
        buildInvalidForecast('2', mockForDate, 2, 'two')
      ])
      expect(res).toHaveLength(1)
      expect(res[0].id).toBe('1')
    })
    it('should filter out N/A forecasts', () => {
      const res = getRowsToSave([
        buildCompleteForecast('1', mockForDate, 1, 'one'),
        buildNAForecast('2', mockForDate, 2, 'two')
      ])
      expect(res).toHaveLength(1)
      expect(res[0].id).toBe('1')
    })
    it('should filter out rows with actuals', () => {
      const forecastWithActual = buildCompleteForecast('2', mockForDate, 2, 'two')
      forecastWithActual.precipActual = 1
      const res = getRowsToSave([
        buildCompleteForecast('1', mockForDate, 1, 'one'),
        buildForecastWithActuals('2', mockForDate, 2, 'two')
      ])
      expect(res).toHaveLength(1)
      expect(res[0].id).toBe('1')
    })
  })
})
