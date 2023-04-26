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
  row.precipForecast.choice !== '' &&
  !isUndefined(row.rhForecast) &&
  row.rhForecast.choice !== '' &&
  !isUndefined(row.tempForecast) &&
  row.tempForecast.choice !== '' &&
  !isUndefined(row.windSpeedForecast) &&
  row.windSpeedForecast.choice !== ''

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
    precip: r.precipForecast || { choice: '', value: NaN },
    rh: r.rhForecast || { choice: '', value: NaN },
    temp: r.tempForecast || { choice: '', value: NaN },
    windDirection: r.windDirectionForecast || { choice: '', value: NaN },
    windSpeed: r.windSpeedForecast || { choice: '', value: NaN }
  }))
}
