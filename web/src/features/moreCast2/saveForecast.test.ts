import { ModelChoice } from 'api/moreCast2API'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { getRowsToSave, isForecastValid } from 'features/moreCast2/saveForecasts'
import { validForecastPredicate } from 'features/moreCast2/util'
import { DateTime } from 'luxon'

const baseRow = {
  precipActual: NaN,
  precipGDPS: 0,
  precipGDPS_BIAS: 0,
  precipGFS: 0,
  precipGFS_BIAS: 0,
  precipHRDPS: 0,
  precipHRDPS_BIAS: 0,
  precipNAM: 0,
  precipNAM_BIAS: 0,
  precipRDPS: 0,
  precipRDPS_BIAS: 0,
  rhActual: NaN,
  rhGDPS: 0,
  rhGDPS_BIAS: 0,
  rhGFS: 0,
  rhGFS_BIAS: 0,
  rhHRDPS: 0,
  rhHRDPS_BIAS: 0,
  rhNAM: 0,
  rhNAM_BIAS: 0,
  rhRDPS: 0,
  rhRDPS_BIAS: 0,
  tempActual: NaN,
  tempGDPS: 0,
  tempGDPS_BIAS: 0,
  tempGFS: 0,
  tempGFS_BIAS: 0,
  tempHRDPS: 0,
  tempHRDPS_BIAS: 0,
  tempNAM: 0,
  tempNAM_BIAS: 0,
  tempRDPS: 0,
  tempRDPS_BIAS: 0,
  windDirectionActual: NaN,
  windDirectionGDPS: 0,
  windDirectionGDPS_BIAS: 0,
  windDirectionGFS: 0,
  windDirectionGFS_BIAS: 0,
  windDirectionNAM: 0,
  windDirectionNAM_BIAS: 0,
  windDirectionHRDPS: 0,
  windDirectionHRDPS_BIAS: 0,
  windDirectionRDPS: 0,
  windDirectionRDPS_BIAS: 0,
  windSpeedActual: NaN,
  windSpeedGDPS: 0,
  windSpeedGDPS_BIAS: 0,
  windSpeedGFS: 0,
  windSpeedGFS_BIAS: 0,
  windSpeedHRDPS: 0,
  windSpeedHRDPS_BIAS: 0,
  windSpeedNAM: 0,
  windSpeedNAM_BIAS: 0,
  windSpeedRDPS: 0,
  windSpeedRDPS_BIAS: 0,
  ffmcCalcActual: 0,
  dmcCalcActual: 0,
  dcCalcActual: 0,
  isiCalcActual: 0,
  buiCalcActual: 0,
  fwiCalcActual: 0,
  dgrCalcActual: 0
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
  stationName: string,
  latitude: number,
  longitude: number
): MoreCast2Row => ({
  id,
  forDate,
  stationCode,
  stationName,
  latitude,
  longitude,
  ...baseRow,
  precipForecast: { choice: ModelChoice.GDPS, value: 0 },
  rhForecast: { choice: ModelChoice.GDPS, value: 0 },
  tempForecast: { choice: ModelChoice.GDPS, value: 0 },
  windDirectionForecast: { choice: ModelChoice.GDPS, value: 0 },
  windSpeedForecast: { choice: ModelChoice.GDPS, value: 0 }
})

const buildForecastMissingWindDirection = (
  id: string,
  forDate: DateTime,
  stationCode: number,
  stationName: string,
  latitude: number,
  longitude: number
): MoreCast2Row => ({
  id,
  forDate,
  stationCode,
  stationName,
  latitude,
  longitude,
  ...baseRow,
  precipForecast: { choice: ModelChoice.GDPS, value: 0 },
  rhForecast: { choice: ModelChoice.GDPS, value: 0 },
  tempForecast: { choice: ModelChoice.GDPS, value: 0 },
  windDirectionForecast: { choice: ModelChoice.NULL, value: NaN },
  windSpeedForecast: { choice: ModelChoice.GDPS, value: 0 }
})

const buildInvalidForecast = (
  id: string,
  forDate: DateTime,
  stationCode: number,
  stationName: string,
  latitude: number,
  longitude: number
): MoreCast2Row => ({
  id,
  forDate,
  stationCode,
  stationName,
  latitude,
  longitude,
  ...baseRow
})

const buildNAForecast = (
  id: string,
  forDate: DateTime,
  stationCode: number,
  stationName: string,
  latitude: number,
  longitude: number
): MoreCast2Row => ({
  id,
  forDate,
  stationCode,
  stationName,
  latitude,
  longitude,
  ...baseRow,
  precipForecast: { choice: ModelChoice.NULL, value: NaN },
  rhForecast: { choice: ModelChoice.NULL, value: NaN },
  tempForecast: { choice: ModelChoice.NULL, value: NaN },
  windDirectionForecast: { choice: ModelChoice.NULL, value: NaN },
  windSpeedForecast: { choice: ModelChoice.NULL, value: NaN }
})

const buildForecastWithActuals = (
  id: string,
  forDate: DateTime,
  stationCode: number,
  stationName: string,
  latitude: number,
  longitude: number
): MoreCast2Row => ({
  id,
  forDate,
  stationCode,
  stationName,
  latitude,
  longitude,
  ...baseRowWithActuals,
  precipForecast: { choice: ModelChoice.GDPS, value: 0 },
  rhForecast: { choice: ModelChoice.GDPS, value: 0 },
  tempForecast: { choice: ModelChoice.GDPS, value: 0 },
  windDirectionForecast: { choice: ModelChoice.GDPS, value: 0 },
  windSpeedForecast: { choice: ModelChoice.GDPS, value: 0 }
})

describe('saveForecasts', () => {
  describe('isForecastValid', () => {
    it('should return true if all forecasts fields are set', () => {
      expect(
        isForecastValid([
          buildCompleteForecast('1', mockForDate, 1, 'one', 1, 1),
          buildCompleteForecast('2', mockForDate, 2, 'two', 2, 2)
        ])
      ).toBe(true)
    })
    it('should return true if all forecasts fields are set except windDirectionForecast', () => {
      expect(
        isForecastValid([
          buildForecastMissingWindDirection('1', mockForDate, 1, 'one', 1, 1),
          buildForecastMissingWindDirection('2', mockForDate, 2, 'two', 2, 2)
        ])
      ).toBe(true)
    })

    it('should return false if any forecasts have missing forecast fields', () => {
      expect(
        isForecastValid([
          buildCompleteForecast('1', mockForDate, 1, 'one', 1, 1),
          buildInvalidForecast('2', mockForDate, 2, 'two', 2, 2)
        ])
      ).toBe(false)
    })

    it('should return false if any forecasts have missing forecast fields set other than windDirectionForecast', () => {
      expect(isForecastValid([buildNAForecast('1', mockForDate, 2, 'one', 1, 1)])).toBe(false)
    })
  })
  describe('validForecastPredicate', () => {
    it('should return false for a forecast with missing forecast fields', () => {
      expect(validForecastPredicate(buildInvalidForecast('1', mockForDate, 1, 'one', 1, 1))).toBe(false)
    })
    it('should return false for a forecast with forecasts but N/A values', () => {
      expect(validForecastPredicate(buildNAForecast('1', mockForDate, 1, 'one', 1, 1))).toBe(false)
    })
  })
  describe('getRowsToSave', () => {
    it('should filter out invalid forecasts', () => {
      const res = getRowsToSave([
        buildCompleteForecast('1', mockForDate, 1, 'one', 1, 1),
        buildInvalidForecast('2', mockForDate, 2, 'two', 2, 2)
      ])
      expect(res).toHaveLength(1)
      expect(res[0].id).toBe('1')
    })
    it('should filter out N/A forecasts', () => {
      const res = getRowsToSave([
        buildCompleteForecast('1', mockForDate, 1, 'one', 1, 1),
        buildNAForecast('2', mockForDate, 2, 'two', 2, 2)
      ])
      expect(res).toHaveLength(1)
      expect(res[0].id).toBe('1')
    })
    it('should filter out rows with actuals', () => {
      const forecastWithActual = buildCompleteForecast('2', mockForDate, 2, 'two', 2, 2)
      forecastWithActual.precipActual = 1
      const res = getRowsToSave([
        buildCompleteForecast('1', mockForDate, 1, 'one', 1, 1),
        buildForecastWithActuals('2', mockForDate, 2, 'two', 2, 2)
      ])
      expect(res).toHaveLength(1)
      expect(res[0].id).toBe('1')
    })
  })
})
