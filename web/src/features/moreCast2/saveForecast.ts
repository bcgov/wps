import { MoreCast2ForecastRow, MoreCast2Row } from 'features/moreCast2/interfaces'
import { isEmpty, isUndefined } from 'lodash'

export const validForecastPredicate = (row: MoreCast2Row) =>
  !isUndefined(row.precipForecast) &&
  row.precipForecast.choice !== '' &&
  !isUndefined(row.rhForecast) &&
  row.rhForecast.choice !== '' &&
  !isUndefined(row.tempForecast) &&
  row.tempForecast.choice !== '' &&
  !isUndefined(row.windDirectionForecast) &&
  row.windDirectionForecast.choice !== '' &&
  !isUndefined(row.windSpeedForecast) &&
  row.windSpeedForecast.choice !== ''

export const isForecastValid = (rows: MoreCast2Row[]) => {
  return !isEmpty(getRowsToSave(rows))
}

export const getRowsToSave = (rows: MoreCast2Row[]): MoreCast2ForecastRow[] => {
  return rows.filter(validForecastPredicate).map(r => ({
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
