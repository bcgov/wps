import _ from 'lodash'
import {
  PRECIP_VALUES_DECIMAL,
  RH_VALUES_DECIMAL,
  TEMPERATURE_VALUES_DECIMAL,
  WIND_SPEED_VALUES_DECIMAL
} from 'utils/constants'
import { WeatherValue } from 'features/fireWeather/components/tables/SortableTableByDatetime'

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

export const getMinMaxValueCalculator = (rows: WeatherValue[]): MinMaxValues => {
  return {
    relative_humidity: _.minBy(rows, 'relative_humidity')?.relative_humidity ?? null,
    wind_speed: _.maxBy(rows, 'wind_speed')?.wind_speed ?? null,
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
      row.wind_speed?.toFixed(WIND_SPEED_VALUES_DECIMAL) ===
      minMaxValuesToHighlight.wind_speed?.toFixed(WIND_SPEED_VALUES_DECIMAL)
    ) {
      rowIds['wind'].push(idx)
    }
  })

  return rowIds
}
