import { isNumber } from 'lodash'
import { DateTime } from 'luxon'
import { ModelType, StationPrediction } from 'api/moreCast2API'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'

// Convert the model predictions from the API to a format that can be used by the data grid
export const parseModelsForStationsHelper = (predictions: StationPrediction[]) => {
  const rows: MoreCast2ForecastRow[] = []

  predictions.forEach(prediction => {
    const station_code = prediction.station.code
    const station_name = prediction.station.name
    const model = prediction.model as ModelType
    const row: MoreCast2ForecastRow = {
      id: prediction.id,
      forDate: DateTime.fromISO(prediction.datetime),
      precip: {
        choice: model,
        value: isNumber(prediction.precip_24hours) ? prediction.precip_24hours : NaN
      },
      rh: {
        choice: model,
        value: isNumber(prediction.relative_humidity) ? prediction.relative_humidity : NaN
      },
      stationCode: station_code,
      stationName: station_name,
      temp: {
        choice: model,
        value: isNumber(prediction.temperature) ? prediction.temperature : NaN
      },
      windDirection: {
        choice: model,
        value: isNumber(prediction.wind_direction) ? prediction.wind_direction : NaN
      },
      windSpeed: {
        choice: model,
        value: isNumber(prediction.wind_speed) ? prediction.wind_speed : NaN
      }
    }
    rows.push(row)
  })
  return rows
}
