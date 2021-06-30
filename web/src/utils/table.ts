import _ from 'lodash'
import { DateTime } from 'luxon'
import {
  PRECIP_VALUES_DECIMAL,
  RH_VALUES_DECIMAL,
  TEMPERATURE_VALUES_DECIMAL,
  WIND_SPEED_VALUES_DECIMAL
} from 'utils/constants'
import { ModelValue } from 'api/modelAPI'
import { ObservedValue } from 'api/observationAPI'
import {
  WeatherValue,
  Column
} from 'features/fireWeather/components/tables/SortableTableByDatetime'

export type Order = 'asc' | 'desc'

export interface MinMaxValues {
  relative_humidity: number | null
  precipitation: number | null
  wind_speed: number | null
  temperature: {
    min: number | null
    max: number | null
  }
}

export interface RowIdsOfMinMaxValues {
  relative_humidity: number[]
  precipitation: number[]
  wind: number[]
  max_temp: number[]
  min_temp: number[]
}

// More generic approach https://material-ui.com/components/tables/#EnhancedTable.tsx
export const getDatetimeComparator = (order: Order) => <T extends { datetime: string }>(
  a: T,
  b: T
): number => {
  const aDate = new Date(a.datetime)
  const bDate = new Date(b.datetime)
  const diff = aDate.valueOf() - bDate.valueOf()

  return order === 'asc' ? diff : -diff
}

const calculateMaxPrecip = (rows: WeatherValue[]): number | null => {
  // calculates the maximum precip value from a set of table rows (assuming that
  // the precip property is named one of 'precipitation', 'delta_precipitation',
  // or 'total_precipitation'). Returns null if none of these properties can be
  // found in props.rows, or if no precip values are set in the rows, or if the
  // maximum value is 0
  let maxPrecip = null
  if (_.maxBy(rows, 'precipitation') !== undefined) {
    maxPrecip = _.maxBy(rows, 'precipitation')?.precipitation
  } else if (_.maxBy(rows, 'delta_precipitation') !== undefined) {
    maxPrecip = _.maxBy(rows, 'delta_precipitation')?.delta_precipitation
  } else if (_.maxBy(rows, 'total_precipitation') !== undefined) {
    maxPrecip = _.maxBy(rows, 'total_precipitation')?.total_precipitation
  }
  maxPrecip = maxPrecip ?? null
  if (maxPrecip !== null && maxPrecip.toFixed(PRECIP_VALUES_DECIMAL) !== '0.0') {
    return maxPrecip
  } else {
    return null
  }
}

export interface AccumulatedPrecipitation {
  precipitation: number | undefined
  values: (ModelValue | ObservedValue)[]
}

export const calculateAccumulatedPrecip = (
  noonDate: string,
  collection: ModelValue[] | ObservedValue[] | undefined
): AccumulatedPrecipitation | undefined => {
  // We are calculating the accumulated precipitation from 24 hours before noon.
  const from = DateTime.fromISO(noonDate).toJSDate()
  from.setHours(from.getHours() - 24)
  const to = DateTime.fromISO(noonDate).toJSDate()
  if (collection) {
    const precip = {
      precipitation: undefined,
      values: [] as (ModelValue | ObservedValue)[]
    } as AccumulatedPrecipitation
    collection.forEach((value: ModelValue | ObservedValue) => {
      const precipDate = DateTime.fromISO(value.datetime).toJSDate()
      if (precipDate > from && precipDate <= to) {
        let precipitate = undefined
        if ('delta_precipitation' in value) {
          precipitate = value.delta_precipitation
        } else if ('precipitation' in value) {
          precipitate = value.precipitation
        }
        if (typeof precipitate === 'number') {
          if (precip.precipitation === undefined) {
            precip.precipitation = precipitate
          } else {
            precip.precipitation += precipitate
          }
          // Keep track of the model run predictions used to calculate this.
          precip.values.push(value)
        }
      }
    })
    return precip
  }
  return undefined
}

const calculateMaxWindSpeed = (rows: WeatherValue[]): number | null => {
  // calculates the maximum wind speed from a set of table rows.
  // Returns null if the maximum value is 0.0 (since we don't want every
  // wind cell in the table to be highlighted).
  const maxWindSpeed = _.maxBy(rows, 'wind_speed')?.wind_speed ?? null
  if (
    maxWindSpeed !== null &&
    maxWindSpeed.toFixed(WIND_SPEED_VALUES_DECIMAL) !== '0.0'
  ) {
    return maxWindSpeed
  } else {
    return null
  }
}

export const getMinMaxValueCalculator = (rows: WeatherValue[]): MinMaxValues => {
  return {
    relative_humidity: _.minBy(rows, 'relative_humidity')?.relative_humidity ?? null,
    wind_speed: calculateMaxWindSpeed(rows),
    temperature: {
      min: _.minBy(rows, 'temperature')?.temperature ?? null,
      max: _.maxBy(rows, 'temperature')?.temperature ?? null
    },
    precipitation: calculateMaxPrecip(rows)
  }
}

export const getMinMaxValuesRowIds = (
  rows: WeatherValue[],
  minMaxValuesToHighlight: MinMaxValues
): RowIdsOfMinMaxValues => {
  const rowIds: RowIdsOfMinMaxValues = {
    relative_humidity: [],
    precipitation: [],
    wind: [],
    max_temp: [],
    min_temp: []
  }

  rows.forEach((row, idx) => {
    if (
      row.relative_humidity?.toFixed(RH_VALUES_DECIMAL) ===
      minMaxValuesToHighlight.relative_humidity?.toFixed(RH_VALUES_DECIMAL)
    ) {
      rowIds['relative_humidity'].push(idx)
    }
    if (
      // max precip value may be null if all precip values in props.rows were 0
      minMaxValuesToHighlight.precipitation !== null &&
      (row.precipitation?.toFixed(PRECIP_VALUES_DECIMAL) ===
        minMaxValuesToHighlight.precipitation?.toFixed(PRECIP_VALUES_DECIMAL) ||
        row.delta_precipitation?.toFixed(PRECIP_VALUES_DECIMAL) ===
          minMaxValuesToHighlight.precipitation?.toFixed(PRECIP_VALUES_DECIMAL) ||
        row.total_precipitation?.toFixed(PRECIP_VALUES_DECIMAL) ===
          minMaxValuesToHighlight.precipitation?.toFixed(PRECIP_VALUES_DECIMAL))
    ) {
      rowIds['precipitation'].push(idx)
    }
    if (
      row.temperature?.toFixed(TEMPERATURE_VALUES_DECIMAL) ===
      minMaxValuesToHighlight.temperature.max?.toFixed(TEMPERATURE_VALUES_DECIMAL)
    ) {
      rowIds['max_temp'].push(idx)
    }
    if (
      row.temperature?.toFixed(TEMPERATURE_VALUES_DECIMAL) ===
      minMaxValuesToHighlight.temperature.min?.toFixed(TEMPERATURE_VALUES_DECIMAL)
    ) {
      rowIds['min_temp'].push(idx)
    }
    if (
      minMaxValuesToHighlight.wind_speed !== null &&
      row.wind_speed?.toFixed(WIND_SPEED_VALUES_DECIMAL) ===
        minMaxValuesToHighlight.wind_speed?.toFixed(WIND_SPEED_VALUES_DECIMAL)
    ) {
      rowIds['wind'].push(idx)
    }
  })

  return rowIds
}

export const getCellClassNameAndTestId = (
  column: Column,
  rowIds: RowIdsOfMinMaxValues,
  idx: number,
  classes: Record<string, string>
): { className: string | undefined; testId: string | undefined } => {
  let className = undefined
  let testId = undefined
  switch (column.id) {
    case 'relative_humidity': {
      if (rowIds['relative_humidity'].includes(idx)) {
        className = classes.minRH
        testId = `min-RH-td`
      }
      break
    }
    case 'temperature': {
      if (rowIds['min_temp'].includes(idx)) {
        className = classes.minTemperature
        testId = `min-temperature-td`
      } else if (rowIds['max_temp'].includes(idx)) {
        className = classes.maxTemperature
        testId = `max-temperature-td`
      }
      break
    }
    case 'precipitation':
    case 'delta_precipitation':
    case 'total_precipitation': {
      if (rowIds['precipitation'].includes(idx)) {
        className = classes.maxPrecipitation
        testId = `max-precipitation-td`
      }
      break
    }
    case 'wind_speed': {
      if (rowIds['wind'].includes(idx)) {
        className = classes.maxWindSpeed
        testId = `max-wind-speed-td`
      }
      break
    }
    case 'wind_direction': {
      if (rowIds['wind'].includes(idx)) {
        className = classes.directionOfMaxWindSpeed
        testId = `direction-max-wind-speed-td`
      }
      break
    }
  }
  return { className, testId }
}
