import { FBAStation } from 'api/fbaCalcAPI'
import assert from 'assert'
import { GridMenuOption, FBAInputRow } from 'features/fbaCalculator/components/FBATable'
import { formatCrownFractionBurned } from 'features/fbaCalculator/components/CrownFractionBurnedCell'
import { formatCriticalHoursAsString } from 'features/fbaCalculator/components/CriticalHoursCell'
import { FuelTypes } from 'features/fbaCalculator/fuelTypes'
import _, { isNull, isUndefined, merge, uniqBy } from 'lodash'
import { Order } from 'utils/table'
export enum SortByColumn {
  Zone,
  Station,
  Elevation,
  FuelType,
  GrassCure,
  Status,
  Temperature,
  RelativeHumidity,
  WindDirection,
  WindSpeed,
  Precipitation,
  FFMC,
  DMC,
  DC,
  ISI,
  BUI,
  FWI,
  HFI,
  CriticalHours4000,
  CriticalHours10000,
  ROS,
  FireType,
  CFB,
  FlameLength,
  ThirtyMinFireSize,
  SixtyMinFireSize
}

// the number of decimal places to round to
const DECIMAL_PLACES = 1

export interface DisplayableInputRow {
  id: number
  weatherStation: GridMenuOption | null
  fuelType: GridMenuOption | null
  grassCure: number | undefined
  windSpeed: number | undefined
}

export type FBATableRow = DisplayableInputRow & Partial<FBAStation>

export class RowManager {
  public static sortRows = (
    sortByColumn: SortByColumn,
    order: Order,
    tableRows: FBATableRow[]
  ): FBATableRow[] => {
    const reverseOrder = order === 'asc' ? 'desc' : 'asc'
    switch (sortByColumn) {
      case SortByColumn.Zone: {
        return _.orderBy(tableRows, 'zone_code', order)
      }
      case SortByColumn.Station: {
        return _.orderBy(tableRows, 'station_name', order)
      }
      case SortByColumn.Elevation: {
        return _.orderBy(tableRows, 'elevation', order)
      }
      case SortByColumn.FuelType: {
        return _.orderBy(tableRows, 'fuel_type', order)
      }
      case SortByColumn.GrassCure: {
        return _.orderBy(tableRows, 'grass_cure', order)
      }
      case SortByColumn.Status: {
        return _.orderBy(tableRows, 'status', order)
      }
      case SortByColumn.Temperature: {
        return _.orderBy(tableRows, 'temp', order)
      }
      case SortByColumn.RelativeHumidity: {
        return _.orderBy(tableRows, 'rh', order)
      }
      case SortByColumn.WindDirection: {
        return _.orderBy(tableRows, 'wind_direction', order)
      }
      case SortByColumn.WindSpeed: {
        return _.orderBy(tableRows, 'wind_speed', order)
      }
      case SortByColumn.Precipitation: {
        return _.orderBy(tableRows, 'precipitation', order)
      }
      case SortByColumn.FFMC: {
        return _.orderBy(tableRows, 'fine_fuel_moisture_code', order)
      }
      case SortByColumn.DMC: {
        return _.orderBy(tableRows, 'duff_moisture_code', order)
      }
      case SortByColumn.DC: {
        return _.orderBy(tableRows, 'drought_code', order)
      }
      case SortByColumn.ISI: {
        return _.orderBy(tableRows, 'initial_spread_index', order)
      }
      case SortByColumn.BUI: {
        return _.orderBy(tableRows, 'build_up_index', order)
      }
      case SortByColumn.FWI: {
        return _.orderBy(tableRows, 'fire_weather_index', order)
      }
      case SortByColumn.HFI: {
        return _.orderBy(tableRows, 'head_fire_intensity', order)
      }
      case SortByColumn.CriticalHours4000: {
        return _.orderBy(tableRows, 'critical_hours_hfi_4000.start', reverseOrder)
      }
      case SortByColumn.CriticalHours10000: {
        return _.orderBy(tableRows, 'critical_hours_hfi_10000.start', reverseOrder)
      }
      case SortByColumn.ThirtyMinFireSize: {
        return _.orderBy(tableRows, 'thirty_minute_fire_size', order)
      }
      case SortByColumn.SixtyMinFireSize: {
        return _.orderBy(tableRows, 'sixty_minute_fire_size', order)
      }
      case SortByColumn.ROS: {
        return _.orderBy(tableRows, 'rate_of_spread', order)
      }
      case SortByColumn.FireType: {
        return _.orderBy(tableRows, 'fire_type', order)
      }
      case SortByColumn.CFB: {
        return _.orderBy(tableRows, 'percentage_crown_fraction_burned', order)
      }
      case SortByColumn.FlameLength: {
        return _.orderBy(tableRows, 'flame_length', order)
      }

      default: {
        return tableRows
      }
    }
  }
  public static updateRows<T extends { id: number }>(
    existingRows: Array<T>,
    updatedCalculatedRows: FBAStation[]
  ): Array<T> {
    const rows = [...existingRows]
    const updatedRowById = new Map(updatedCalculatedRows.map(row => [row.id, row]))
    const mergedRows = rows.map(row => {
      if (updatedRowById.has(row.id)) {
        const mergedRow = merge(row, updatedRowById.get(row.id))
        updatedRowById.delete(row.id)
        return mergedRow
      }
      return row
    })

    assert(mergedRows.length === uniqBy(mergedRows, 'id').length)
    return mergedRows
  }

  public static buildFBATableRow = (
    inputRow: FBAInputRow,
    stationCodeMap: Map<string, string>
  ): FBATableRow => ({
    ...inputRow,
    weatherStation: RowManager.buildStationOption(
      inputRow.weatherStation,
      stationCodeMap
    ),
    fuelType: RowManager.buildFuelTypeMenuOption(inputRow.fuelType)
  })

  public static buildStationOption = (
    value: string | undefined,
    stationCodeMap: Map<string, string>
  ): GridMenuOption | null => {
    if (isUndefined(value)) {
      return null
    }
    const label = stationCodeMap.get(value)

    if (isUndefined(label)) {
      return null
    }
    return {
      label,
      value
    }
  }
  public static buildFuelTypeMenuOption = (
    value: string | undefined
  ): GridMenuOption | null => {
    if (isUndefined(value)) {
      return null
    }
    const fuelType = FuelTypes.lookup(value)
    if (isUndefined(fuelType) || isNull(fuelType)) {
      return null
    }
    return {
      label: fuelType.friendlyName,
      value
    }
  }

  public static exportRowsAsStrings = (tableRows: FBATableRow[]): string[][] => {
    const rowsAsStrings: string[][] = []
    tableRows.forEach(value => {
      const rowString: string[] = []
      rowString.push(isUndefined(value.zone_code) ? '' : value.zone_code)
      rowString.push(
        isNull(value.weatherStation) || isUndefined(value.weatherStation.label)
          ? ''
          : value.weatherStation.label
      )
      rowString.push(isUndefined(value.elevation) ? '' : value.elevation.toString())
      rowString.push(isUndefined(value.fuel_type) ? '' : value.fuel_type)
      rowString.push(
        isUndefined(value.grass_cure) ||
          isNaN(value.grass_cure) ||
          isNull(value.grass_cure)
          ? ''
          : value.grass_cure.toString()
      )
      rowString.push(isUndefined(value.status) ? '' : value.status)
      rowString.push(
        isUndefined(value.temp) || isNull(value.temp)
          ? ''
          : value.temp.toFixed(DECIMAL_PLACES)
      )
      rowString.push(isUndefined(value.rh) || isNull(value.rh) ? '' : value.rh.toString())
      rowString.push(
        isUndefined(value.wind_direction) ||
          isNaN(value.wind_direction) ||
          isNull(value.wind_direction)
          ? ''
          : value.wind_direction.toString()
      )
      let formattedWindSpeed = ''
      if (!isUndefined(value.windSpeed) && !isNaN(value.windSpeed) && !isNull(value.windSpeed)) {
        formattedWindSpeed = value.windSpeed.toFixed(DECIMAL_PLACES)
      } else if (!isUndefined(value.wind_speed) && !isNull(value.wind_speed)) {
        formattedWindSpeed = value.wind_speed.toFixed(DECIMAL_PLACES)
      }
      rowString.push(formattedWindSpeed)
      rowString.push(
        isUndefined(value.precipitation) || isNull(value.precipitation)
          ? ''
          : value.precipitation.toFixed(DECIMAL_PLACES)
      )
      rowString.push(
        isUndefined(value.fine_fuel_moisture_code) ||
          isNull(value.fine_fuel_moisture_code)
          ? ''
          : value.fine_fuel_moisture_code.toFixed(DECIMAL_PLACES)
      )
      rowString.push(
        isUndefined(value.duff_moisture_code) || isNull(value.duff_moisture_code)
          ? ''
          : value.duff_moisture_code.toFixed(DECIMAL_PLACES)
      )
      rowString.push(
        isUndefined(value.drought_code) || isNull(value.drought_code)
          ? ''
          : value.drought_code.toFixed(DECIMAL_PLACES)
      )
      rowString.push(
        isUndefined(value.initial_spread_index) || isNull(value.initial_spread_index)
          ? ''
          : value.initial_spread_index.toFixed(DECIMAL_PLACES)
      )
      rowString.push(
        isUndefined(value.build_up_index) || isNull(value.build_up_index)
          ? ''
          : value.build_up_index.toFixed(DECIMAL_PLACES)
      )
      rowString.push(
        isUndefined(value.fire_weather_index) || isNull(value.fire_weather_index)
          ? ''
          : value.fire_weather_index.toFixed(DECIMAL_PLACES)
      )
      rowString.push(
        isUndefined(value.head_fire_intensity) || isNull(value.head_fire_intensity)
          ? ''
          : value.head_fire_intensity.toFixed(DECIMAL_PLACES)
      )
      const criticalHours4000 = formatCriticalHoursAsString(value.critical_hours_hfi_4000)
      rowString.push(
        isUndefined(criticalHours4000) || isNull(criticalHours4000)
          ? ''
          : criticalHours4000
      )
      const criticalHours10000 = formatCriticalHoursAsString(
        value.critical_hours_hfi_10000
      )
      rowString.push(
        isUndefined(criticalHours10000) || isNull(criticalHours10000)
          ? ''
          : criticalHours10000
      )
      rowString.push(
        isUndefined(value.rate_of_spread) || isNull(value.rate_of_spread)
          ? ''
          : value.rate_of_spread.toFixed(DECIMAL_PLACES)
      )
      rowString.push(
        isUndefined(value.fire_type) || isNull(value.fire_type) ? '' : value.fire_type
      )
      const formattedCFB = formatCrownFractionBurned(
        value.percentage_crown_fraction_burned
      )
      rowString.push(
        isUndefined(formattedCFB) || isNull(formattedCFB) ? '' : formattedCFB
      )
      rowString.push(
        isUndefined(value.flame_length) || isNull(value.flame_length)
          ? ''
          : value.flame_length.toFixed(DECIMAL_PLACES)
      )
      rowString.push(
        isUndefined(value.thirty_minute_fire_size) ||
          isNull(value.thirty_minute_fire_size)
          ? ''
          : value.thirty_minute_fire_size.toFixed(DECIMAL_PLACES)
      )
      rowString.push(
        isUndefined(value.sixty_minute_fire_size) || isNull(value.sixty_minute_fire_size)
          ? ''
          : value.sixty_minute_fire_size.toFixed(DECIMAL_PLACES)
      )
      rowsAsStrings.push(rowString)
    })
    return rowsAsStrings
  }
}
