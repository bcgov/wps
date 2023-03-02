import { isNumber } from 'lodash'
import { DateTime, Interval } from 'luxon'
import { FireCenterStation } from 'api/fbaAPI'
import { ModelType, StationPrediction } from 'api/moreCast2API'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'

// Convert the model predictions from the API to a format that can be used by a MoreCast2DataGrid data grid
export const parseModelsForStationsHelper = (predictions: StationPrediction[]): MoreCast2ForecastRow[] => {
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
  return rows.sort((a, b) => a.stationName.localeCompare(b.stationName))
}

export const fillInTheBlanks = (
  stations: FireCenterStation[],
  stationPredictions: StationPrediction[],
  dateInterval: string[],
  modelType: ModelType
) => {
  const missingPredictions: StationPrediction[] = []
  // Iterate through all the station codes and the expected date strings to ensure there is an
  // item in the array for each unique combination
  stations.forEach(station => {
    dateInterval.forEach(date => {
      const filteredPrediction = stationPredictions.filter(p => p.station.code === station.code && p.datetime === date)
      if (!filteredPrediction.length) {
        missingPredictions.push(createEmptyStationPrediction(station.code, date, station.name, modelType))
      }
    })
  })
  // Use .slice() to create a shallow copy of the predictions from the API and add the missing predictions
  const completeStationPredictions: StationPrediction[] = [...missingPredictions, ...stationPredictions.slice()]
  return completeStationPredictions
}

const createEmptyStationPrediction = (
  code: number,
  datetime: string,
  name: string,
  modelType: ModelType
): StationPrediction => {
  const prediction = {
    bias_adjusted_relative_humidity: NaN,
    bias_adjusted_temperature: NaN,
    datetime: datetime,
    precip_24hours: NaN,
    id: window.crypto.randomUUID(),
    model: modelType,
    relative_humidity: NaN,
    station: {
      code,
      name,
      lat: NaN,
      long: NaN,
      ecodivision_name: null,
      core_season: {
        start_month: NaN,
        start_day: NaN,
        end_month: NaN,
        end_day: NaN
      }
    },
    temperature: NaN,
    wind_direction: NaN,
    wind_speed: NaN
  }

  return prediction
}

export const createDateInterval = (fromDate: DateTime, toDate: DateTime) => {
  // Create an array of UTC datetime strings inclusive of the user selected from/to dates
  // This range of UTC datetimes is needed to help determine when a station is missing a
  // row of predictions
  const interval = Interval.fromDateTimes(fromDate, toDate.plus({ days: 1 }))
  const dateTimeArray = interval.splitBy({ day: 1 }).map(d => d.start)
  const dates = dateTimeArray.map(date => {
    return `${date.toISODate()}T20:00:00+00:00`
  })
  return dates
}
