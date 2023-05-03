import { ModelChoice } from 'api/moreCast2API'
import { MoreCast2ForecastRow, MoreCast2Row } from 'features/moreCast2/interfaces'
import { isUndefined } from 'lodash'

// Forecast rows contain all NaN values in their 'actual' fields
export const isForecastRowPredicate = (row: MoreCast2Row) =>
  isNaN(row.precipActual) &&
  isNaN(row.rhActual) &&
  isNaN(row.tempActual) &&
  isNaN(row.windDirectionActual) &&
  isNaN(row.windSpeedActual)

// A valid forecast row has values for precipForecast, rhForecast, tempForecast and windSpeedForecast
export const validForecastPredicate = (row: MoreCast2Row) =>
  !isUndefined(row.precipForecast) &&
  !isNaN(row.precipForecast.value) &&
  !isUndefined(row.rhForecast) &&
  !isNaN(row.rhForecast.value) &&
  !isUndefined(row.tempForecast) &&
  !isNaN(row.tempForecast.value) &&
  !isUndefined(row.windSpeedForecast) &&
  !isNaN(row.windSpeedForecast.value)

export const getForecastRows = (rows: MoreCast2Row[]): MoreCast2Row[] => {
  return rows ? rows.filter(isForecastRowPredicate) : []
}

export const isForecastValid = (rows: MoreCast2Row[]) => {
  const forecastRows = getForecastRows(rows)
  const validForecastRows = forecastRows.filter(validForecastPredicate)
  return forecastRows.length === validForecastRows.length
}

export const getRowsToSave = (rows: MoreCast2Row[]): MoreCast2ForecastRow[] => {
  const forecastRows = getForecastRows(rows)
  const rowsToSave = forecastRows.filter(validForecastPredicate)
  return rowsToSave.map(r => ({
    id: r.id,
    stationCode: r.stationCode,
    stationName: r.stationName,
    forDate: r.forDate,
    precip: r.precipForecast || { choice: ModelChoice.NULL, value: NaN },
    rh: r.rhForecast || { choice: ModelChoice.NULL, value: NaN },
    temp: r.tempForecast || { choice: ModelChoice.NULL, value: NaN },
    windDirection: r.windDirectionForecast || { choice: ModelChoice.NULL, value: NaN },
    windSpeed: r.windSpeedForecast || { choice: ModelChoice.NULL, value: NaN }
  }))
}
