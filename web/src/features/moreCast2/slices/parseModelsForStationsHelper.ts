import { isNumber } from 'lodash'
import { DateTime } from 'luxon'
import { ModelsForStation, ModelValue } from 'api/modelAPI'
import { ModelType } from 'api/moreCast2API'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'

// Convert the model predictions from the API to a format that can be used by the data grid
export const parseModelsForStationsHelper = (stations: ModelsForStation[]) => {
  const rows: MoreCast2ForecastRow[] = []

  stations.forEach(station => {
    const station_code = station.station.code
    const station_name = station.station.name
    const most_recent_model_run = station.model_runs.reduce((a, b) => {
      return DateTime.fromISO(a.model_run.datetime) > DateTime.fromISO(b.model_run.datetime) ? a : b
    })
    const filteredValues = most_recent_model_run.values.filter(value => value.datetime.endsWith('T12:00:00+00:00'))

    const model: ModelType = most_recent_model_run.model_run.abbreviation as ModelType
    filteredValues.forEach((modelValue: ModelValue) => {
      const row: MoreCast2ForecastRow = {
        id: window.crypto.randomUUID(),
        forDate: DateTime.fromISO(modelValue.datetime),
        precip: {
          choice: model,
          value: isNumber(modelValue.delta_precipitation) ? modelValue.delta_precipitation : NaN
        },
        rh: {
          choice: model,
          value: isNumber(modelValue.relative_humidity) ? modelValue.relative_humidity : NaN
        },
        stationCode: station_code,
        stationName: station_name,
        temp: {
          choice: model,
          value: isNumber(modelValue.temperature) ? modelValue.temperature : NaN
        },
        windDirection: {
          choice: model,
          value: isNumber(modelValue.wind_direction) ? modelValue.wind_direction : NaN
        },
        windSpeed: {
          choice: model,
          value: isNumber(modelValue.wind_speed) ? modelValue.wind_speed : NaN
        }
      }
      rows.push(row)
    })
  })
  return rows
}
