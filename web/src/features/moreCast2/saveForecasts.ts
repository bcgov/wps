import { ModelChoice } from 'api/moreCast2API'
import { MoreCast2ForecastRow, MoreCast2Row, PredictionItem } from 'features/moreCast2/interfaces'
import { isNil } from 'lodash'

// Forecast rows contain all NaN values in their 'actual' fields
export const isForecastRowPredicate = (row: MoreCast2Row) =>
  isNaN(row.precipActual) &&
  isNaN(row.rhActual) &&
  isNaN(row.tempActual) &&
  isNaN(row.windDirectionActual) &&
  isNaN(row.windSpeedActual) &&
  isNaN(row.grassCuringActual)

export const getForecastRows = (rows: MoreCast2Row[]): MoreCast2Row[] => {
  return rows ? rows.filter(isForecastRowPredicate) : []
}

export const getRowsToSave = (rows: MoreCast2Row[]): MoreCast2ForecastRow[] => {
  const forecastRows = getForecastRows(rows)
  const rowsToSave = forecastRows.map(r => ({
    id: r.id,
    stationCode: r.stationCode,
    stationName: r.stationName,
    forDate: r.forDate,
    precip: r.precipForecast ?? { choice: ModelChoice.NULL, value: NaN },
    rh: r.rhForecast ?? { choice: ModelChoice.NULL, value: NaN },
    temp: r.tempForecast ?? { choice: ModelChoice.NULL, value: NaN },
    windDirection: r.windDirectionForecast ?? { choice: ModelChoice.NULL, value: NaN },
    windSpeed: r.windSpeedForecast ?? { choice: ModelChoice.NULL, value: NaN },
    grassCuring: r.grassCuringForecast ?? { choice: ModelChoice.NULL, value: NaN }
  }))
  return rowsToSave
}

export const isRequiredInputSet = (rowsToSave: MoreCast2ForecastRow[]) => {
  const isNilPredictionItem = (item?: PredictionItem) => {
    return isNil(item) || isNaN(item.value)
  }
  const res = rowsToSave.every(row => {
    return (
      !isNilPredictionItem(row.precip) &&
      !isNilPredictionItem(row.rh) &&
      !isNilPredictionItem(row.temp) &&
      !isNilPredictionItem(row.windSpeed)
    )
  })

  return res
}
