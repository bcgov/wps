import { FBAStation } from 'api/fbaCalcAPI'
import { GridMenuOption, FBAInputRow } from 'features/fbaCalculator/components/FBATable'
import { FuelTypes } from 'features/fbaCalculator/fuelTypes'
import _, { isNull, isUndefined, zipWith } from 'lodash'
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
  constructor(private readonly stationCodeMap: Map<string, string>) {}

  public mergeFBARows = (
    inputRows: FBAInputRow[],
    calculatedRows: FBAStation[]
  ): FBATableRow[] =>
    zipWith(inputRows, calculatedRows, (inputRow, outputRow) => {
      if (inputRow) {
        return [
          {
            ...this.buildFBCTableRow(inputRow),
            ...outputRow
          }
        ]
      }
      return []
    }).flat()
  public static updateRows<T extends { id: number }>(
    existingRows: Array<T>,
    updatedCalculatedRows: FBAStation[]
  ): Array<T> {
    const rows = [...existingRows]
    const updatedRowById = new Map(updatedCalculatedRows.map(row => [row.id, row]))
    rows.forEach(row => {
      if (updatedRowById.has(row.id)) {
        rows[row.id] = {
          ...row,
          ...updatedRowById.get(row.id)
        }
      }
    })
    return rows
  }
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

  private buildFBCTableRow = (inputRow: FBAInputRow): FBATableRow => ({
    ...inputRow,
    weatherStation: this.buildStationOption(inputRow.weatherStation),
    fuelType: this.buildFuelTypeMenuOption(inputRow.fuelType)
  })

  private buildStationOption = (value: string | undefined): GridMenuOption | null => {
    if (isUndefined(value)) {
      return null
    }
    const label = this.stationCodeMap.get(value)

    if (isUndefined(label)) {
      return null
    }
    return {
      label,
      value
    }
  }
  private buildFuelTypeMenuOption = (
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
