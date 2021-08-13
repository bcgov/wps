import { FBCStation } from 'api/fbCalcAPI'
import {
  GridMenuOption,
  FBAInputRow
} from 'features/fbaCalculator/components/FBAInputGrid'
import { FuelTypes } from 'features/fbaCalculator/fuelTypes'
import _, { isNull, isUndefined, zipWith } from 'lodash'
import { Order } from 'utils/table'
export enum SortByColumn {
  Zone,
  Station,
  FuelType,
  ISI,
  HFI,
  WindSpeed
}

export interface DisplayableInputRow {
  weatherStation: GridMenuOption | null
  fuelType: GridMenuOption | null
  grassCure: number | undefined
  windSpeed: number | undefined
}

export type FBCTableRow = DisplayableInputRow & Partial<FBCStation>

export class RowManager {
  constructor(private readonly stationCodeMap: Map<string, string>) {}

  mergeFBARows = (
    inputRows: FBAInputRow[],
    calculatedRows: FBCStation[]
  ): FBCTableRow[] =>
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
  public static sortRows = (
    sortByColumn: SortByColumn,
    order: Order,
    tableRows: FBCTableRow[]
  ): FBCTableRow[] => {
    switch (sortByColumn) {
      case SortByColumn.Zone: {
        return _.orderBy(tableRows, 'zone_code', order)
      }
      case SortByColumn.Station: {
        return _.orderBy(tableRows, 'station_name', order)
      }
      case SortByColumn.FuelType: {
        return _.orderBy(tableRows, 'fuel_type', order)
      }
      case SortByColumn.HFI: {
        return _.orderBy(tableRows, 'head_fire_intensity', order)
      }
      case SortByColumn.ISI: {
        return _.orderBy(tableRows, 'initial_spread_index', order)
      }
      case SortByColumn.WindSpeed: {
        return _.orderBy(tableRows, 'wind_speed', order)
      }
      default: {
        return tableRows
      }
    }
  }

  buildFBCTableRow = (inputRow: FBAInputRow): FBCTableRow => ({
    ...inputRow,
    weatherStation: this.buildStationOption(inputRow.weatherStation),
    fuelType: this.buildFuelTypeMenuOption(inputRow.fuelType)
  })

  buildStationOption = (value: string | undefined): GridMenuOption | null => {
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
  buildFuelTypeMenuOption = (value: string | undefined): GridMenuOption | null => {
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
