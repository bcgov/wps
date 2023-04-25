import { isNumber, isUndefined } from 'lodash'
import { DateTime, Interval } from 'luxon'
import { ModelChoice, ModelType, MoreCast2ForecastRecord, StationPrediction } from 'api/moreCast2API'
import { MoreCast2ForecastRow, MoreCast2ForecastRowsByDate } from 'features/moreCast2/interfaces'
import { StationGroupMember } from 'api/stationAPI'

export const parseForecastsHelper = (
  forecasts: MoreCast2ForecastRecord[],
  stations: StationGroupMember[]
): MoreCast2ForecastRow[] => {
  const rows: MoreCast2ForecastRow[] = []

  forecasts.forEach(forecast => {
    const row: MoreCast2ForecastRow = {
      id: rowIDHasher(forecast.station_code, DateTime.fromMillis(forecast.for_date)),
      forDate: DateTime.fromMillis(forecast.for_date),
      precip: {
        choice: ModelChoice.FORECAST,
        value: forecast.precip
      },
      rh: {
        choice: ModelChoice.FORECAST,
        value: forecast.rh
      },
      stationCode: forecast.station_code,
      stationName: stations.find(station => station.station_code === forecast.station_code)?.display_label || '',
      temp: {
        choice: ModelChoice.FORECAST,
        value: forecast.temp
      },
      windDirection: {
        choice: ModelChoice.FORECAST,
        value: forecast.wind_direction || NaN
      },
      windSpeed: {
        choice: ModelChoice.FORECAST,
        value: forecast.wind_speed
      }
    }
    rows.push(row)
  })
  return rows
}

export const buildListOfRowsToDisplay = (
  stationCodesDict: { [stationCode: number]: MoreCast2ForecastRowsByDate[] },
  selectedStations: StationGroupMember[]
): MoreCast2ForecastRow[] => {
  const rowsToDisplay: MoreCast2ForecastRow[] = []

  selectedStations.forEach(station => {
    stationCodesDict[station.station_code]?.forEach(rowsForDate => {
      if (rowsForDate.rows.length === 1) {
        rowsToDisplay.push(rowsForDate.rows[0])
      } else {
        const forecastRows = rowsForDate.rows
        // possibly incomplete logic. Atm we want to prioritize Actuals over any other data source
        // Later on we will probably want additional logic for further prioritization of data sources
        // (e.g., HRDPS takes precedence over GDPS)
        const actualsRow = forecastRows.filter(row => row.temp.choice === ModelChoice.ACTUAL)[0]
        if (!isUndefined(actualsRow)) {
          rowsToDisplay.push(actualsRow)
        }
      }
    })
  })

  rowsToDisplay.sort((a, b) => (a.forDate < b.forDate ? -1 : 1))
  return rowsToDisplay
}

// Convert the model predictions from the API to a format that can be used by a MoreCast2DataGrid data grid
export const parseModelsForStationsHelper = (predictions: StationPrediction[]): MoreCast2ForecastRow[] => {
  const rows: MoreCast2ForecastRow[] = []

  predictions.forEach(prediction => {
    const station_code = prediction.station.code
    const station_name = prediction.station.name
    const model = prediction.abbreviation
    const row: MoreCast2ForecastRow = {
      id: rowIDHasher(prediction.station.code, DateTime.fromISO(prediction.datetime)),
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

const createEmptyStationPrediction = (
  code: number,
  datetime: string,
  name: string,
  modelType: ModelType
): StationPrediction => {
  const prediction = {
    abbreviation: modelType,
    bias_adjusted_relative_humidity: NaN,
    bias_adjusted_temperature: NaN,
    datetime: datetime,
    precip_24hours: NaN,
    id: rowIDHasher(code, DateTime.fromISO(datetime)),
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

/**
 * Returns a unique ID by simply concatenating stationCode and timestamp
 * @param stationCode
 * @param timestamp
 * @returns String concatenation of stationCode and timestamp as an ID
 */
export const rowIDHasher = (stationCode: number, timestamp: DateTime) =>
  `${stationCode}${timestamp.startOf('day').toISODate()}`

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

/**
 * Filters an array of MoreCast2ForecastRows to the subset of elements that do not contain a property
 * with a model choice that matches the specified model type.
 * @param rows The array of MoreCast2ForecastRows to filter
 * @param choice The ModelType to exclude from returned rows
 * @returns A filtered array of MoreCast2ForecastRows
 */
export const excludeRowsByModelType = (rows: MoreCast2ForecastRow[], choice: ModelType) => {
  const filteredRows: MoreCast2ForecastRow[] = []
  rows.forEach(row => {
    if (
      row.precip.choice !== choice &&
      row.rh.choice !== choice &&
      row.temp.choice !== choice &&
      row.windDirection.choice !== choice &&
      row.windSpeed.choice !== choice
    )
      filteredRows.push(row)
  })
  return filteredRows
}
