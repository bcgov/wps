import { ModelChoice } from 'api/moreCast2API'
import { MoreCast2ForecastRow, MoreCast2Row } from 'features/moreCast2/interfaces'
import { getRowsToSave, isRequiredInputSet } from 'features/moreCast2/saveForecasts'
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
  dgrCalcActual: 0,
  grassCuringActual: NaN
}

const baseRowWithActuals = {
  ...baseRow,
  precipActual: 0,
  rhActual: 0,
  tempActual: 0,
  windDirectionActual: 0,
  windSpeedActual: 0,
  grassCuringActual: 0
}

const mockForDate = DateTime.fromISO('2023-02-16T20:00:00+00:00')

const buildCompleteForecast = (
  id: string,
  forDate: DateTime,
  stationCode: number,
  stationName: string
): MoreCast2ForecastRow => ({
  id,
  forDate,
  stationCode,
  stationName,
  ...baseRow,
  precip: { choice: ModelChoice.GDPS, value: 0 },
  rh: { choice: ModelChoice.GDPS, value: 0 },
  temp: { choice: ModelChoice.GDPS, value: 0 },
  windDirection: { choice: ModelChoice.GDPS, value: 0 },
  windSpeed: { choice: ModelChoice.GDPS, value: 0 },
  grassCuring: { choice: ModelChoice.NULL, value: 0 }
})

const buildForecastMissingWindDirection = (
  id: string,
  forDate: DateTime,
  stationCode: number,
  stationName: string
): MoreCast2ForecastRow => ({
  id,
  forDate,
  stationCode,
  stationName,
  ...baseRow,
  precip: { choice: ModelChoice.GDPS, value: 0 },
  rh: { choice: ModelChoice.GDPS, value: 0 },
  temp: { choice: ModelChoice.GDPS, value: 0 },
  windDirection: { choice: ModelChoice.NULL, value: NaN },
  windSpeed: { choice: ModelChoice.GDPS, value: 0 },
  grassCuring: { choice: ModelChoice.NULL, value: 0 }
})

const buildInvalidForecast = (
  id: string,
  forDate: DateTime,
  stationCode: number,
  stationName: string
): MoreCast2ForecastRow => ({
  id,
  forDate,
  stationCode,
  stationName,
  ...baseRow,
  precip: { choice: ModelChoice.NULL, value: NaN },
  rh: { choice: ModelChoice.NULL, value: NaN },
  temp: { choice: ModelChoice.NULL, value: NaN },
  windDirection: { choice: ModelChoice.NULL, value: NaN },
  windSpeed: { choice: ModelChoice.NULL, value: NaN },
  grassCuring: { choice: ModelChoice.NULL, value: NaN }
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
  windSpeedForecast: { choice: ModelChoice.GDPS, value: 0 },
  grassCuringForecast: { choice: ModelChoice.NULL, value: 0 }
})

const buildForecast = (
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
  windSpeedForecast: { choice: ModelChoice.GDPS, value: 0 },
  grassCuringForecast: { choice: ModelChoice.NULL, value: 0 }
})

describe('saveForecasts', () => {
  describe('isForecastValid', () => {
    it('should return true if all forecasts fields are set', () => {
      expect(
        isRequiredInputSet([
          buildCompleteForecast('1', mockForDate, 1, 'one'),
          buildCompleteForecast('2', mockForDate, 2, 'two')
        ])
      ).toBe(true)
    })
    it('should return true if all forecasts fields are set except windDirectionForecast', () => {
      expect(
        isRequiredInputSet([
          buildForecastMissingWindDirection('1', mockForDate, 1, 'one'),
          buildForecastMissingWindDirection('2', mockForDate, 2, 'two')
        ])
      ).toBe(true)
    })

    it('should return false if any forecasts have missing forecast fields', () => {
      expect(
        isRequiredInputSet([
          buildCompleteForecast('1', mockForDate, 1, 'one'),
          buildInvalidForecast('2', mockForDate, 2, 'two')
        ])
      ).toBe(false)
    })

    it('should return false if any forecasts have missing forecast fields set other than windDirectionForecast', () => {
      expect(isRequiredInputSet([buildInvalidForecast('1', mockForDate, 2, 'one')])).toBe(false)
    })
  })
  describe('getRowsToSave', () => {
    it('should filter out rows with actuals', () => {
      const res = getRowsToSave([
        buildForecast('1', mockForDate, 1, 'one', 1, 1),
        buildForecastWithActuals('2', mockForDate, 2, 'two', 2, 2)
      ])
      expect(res).toHaveLength(1)
      expect(res[0].id).toBe('1')
    })
  })
})
