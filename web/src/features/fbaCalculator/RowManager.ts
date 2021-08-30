import { FBAStation } from 'api/fbaCalcAPI'
import assert from 'assert'
import { GridMenuOption, FBAInputRow } from 'features/fbaCalculator/components/FBATable'
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
    const orderByWithEmptyAtBottom = (field: string, otherOrder?: Order) => {
      const partition = _.partition(tableRows, x => !!_.get(x, field, null))
      return _.concat(
        _.orderBy(partition[0], field, otherOrder ? otherOrder : order),
        partition[1]
      )
    }
    switch (sortByColumn) {
      case SortByColumn.Zone: {
        return orderByWithEmptyAtBottom('zone_code')
      }
      case SortByColumn.Station: {
        return orderByWithEmptyAtBottom('station_name')
      }
      case SortByColumn.Elevation: {
        return orderByWithEmptyAtBottom('elevation')
      }
      case SortByColumn.FuelType: {
        return orderByWithEmptyAtBottom('fuel_type')
      }
      case SortByColumn.GrassCure: {
        return orderByWithEmptyAtBottom('grass_cure')
      }
      case SortByColumn.Status: {
        return orderByWithEmptyAtBottom('status')
      }
      case SortByColumn.Temperature: {
        return orderByWithEmptyAtBottom('temp')
      }
      case SortByColumn.RelativeHumidity: {
        return orderByWithEmptyAtBottom('rh')
      }
      case SortByColumn.WindDirection: {
        return orderByWithEmptyAtBottom('wind_direction')
      }
      case SortByColumn.WindSpeed: {
        return orderByWithEmptyAtBottom('wind_speed')
      }
      case SortByColumn.Precipitation: {
        return orderByWithEmptyAtBottom('precipitation')
      }
      case SortByColumn.FFMC: {
        return orderByWithEmptyAtBottom('fine_fuel_moisture_code')
      }
      case SortByColumn.DMC: {
        return orderByWithEmptyAtBottom('duff_moisture_code')
      }
      case SortByColumn.DC: {
        return orderByWithEmptyAtBottom('drought_code')
      }
      case SortByColumn.ISI: {
        return orderByWithEmptyAtBottom('initial_spread_index')
      }
      case SortByColumn.BUI: {
        return orderByWithEmptyAtBottom('build_up_index')
      }
      case SortByColumn.FWI: {
        return orderByWithEmptyAtBottom('fire_weather_index')
      }
      case SortByColumn.HFI: {
        return orderByWithEmptyAtBottom('head_fire_intensity')
      }
      case SortByColumn.CriticalHours4000: {
        return orderByWithEmptyAtBottom('critical_hours_hfi_4000.start', reverseOrder)
      }
      case SortByColumn.CriticalHours10000: {
        return orderByWithEmptyAtBottom('critical_hours_hfi_10000.start', reverseOrder)
      }
      case SortByColumn.ThirtyMinFireSize: {
        return orderByWithEmptyAtBottom('thirty_minute_fire_size')
      }
      case SortByColumn.SixtyMinFireSize: {
        return orderByWithEmptyAtBottom('sixty_minute_fire_size')
      }
      case SortByColumn.ROS: {
        return orderByWithEmptyAtBottom('rate_of_spread')
      }
      case SortByColumn.FireType: {
        return orderByWithEmptyAtBottom('fire_type')
      }
      case SortByColumn.CFB: {
        return orderByWithEmptyAtBottom('percentage_crown_fraction_burned')
      }
      case SortByColumn.FlameLength: {
        return orderByWithEmptyAtBottom('flame_length')
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
}
