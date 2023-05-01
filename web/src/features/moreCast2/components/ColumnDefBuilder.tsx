import {
  GridColDef,
  GridColumnHeaderParams,
  GridRenderCellParams,
  GridValueFormatterParams,
  GridValueGetterParams,
  GridValueSetterParams
} from '@mui/x-data-grid'
import { WeatherDeterminate, WeatherDeterminateType } from 'api/moreCast2API'
import { GridComponentRenderer } from 'features/moreCast2/components/GridComponentRenderer'

export const DEFAULT_COLUMN_WIDTH = 80

// Defines the order in which weather models display in the datagrid.
export const ORDERED_COLUMN_HEADERS: WeatherDeterminateType[] = [
  WeatherDeterminate.ACTUAL,
  WeatherDeterminate.HRDPS,
  WeatherDeterminate.RDPS,
  WeatherDeterminate.GDPS,
  WeatherDeterminate.NAM,
  WeatherDeterminate.GFS
]

export interface ForecastColDefGenerator {
  generateForecastColDef: (headerName?: string) => GridColDef
}

export interface ColDefGenerator {
  generateColDef: (headerName?: string) => GridColDef
  generateColDefs: (headerName?: string) => GridColDef[]
}

export class ColumnDefBuilder implements ColDefGenerator, ForecastColDefGenerator {
  constructor(
    readonly field: string,
    readonly headerName: string,
    readonly type: 'string' | 'number',
    readonly precision: number,
    readonly gridComponentRenderer: GridComponentRenderer
  ) {}

  public generateColDef = () => {
    return this.generateColDefWith(this.field, this.headerName, this.precision, DEFAULT_COLUMN_WIDTH)
  }

  public generateForecastColDef = (headerName?: string) => {
    return this.generateForecastColDefWith(
      `${this.field}${WeatherDeterminate.FORECAST}`,
      headerName ? headerName : this.headerName,
      this.precision,
      DEFAULT_COLUMN_WIDTH
    )
  }

  public generateColDefs = (headerName?: string) => {
    const gridColDefs: GridColDef[] = []
    // Forecast columns have unique requirement (eg. column header menu, editable, etc.)
    const forecastColDef = this.generateForecastColDef(headerName)
    gridColDefs.push(forecastColDef)

    for (const colDef of this.generateNonForecastColDefs()) {
      gridColDefs.push(colDef)
    }

    return gridColDefs
  }

  public generateNonForecastColDefs = () => {
    return ORDERED_COLUMN_HEADERS.map(header =>
      this.generateColDefWith(`${this.field}${header}`, header, this.precision, DEFAULT_COLUMN_WIDTH)
    )
  }

  public generateColDefWith = (field: string, headerName: string, precision: number, width?: number) => {
    return {
      field,
      disableColumnMenu: true,
      disabledReorder: true,
      headerName,
      sortable: false,
      type: 'number',
      width: width ? width : DEFAULT_COLUMN_WIDTH,
      renderCell: (params: Pick<GridRenderCellParams, 'formattedValue'>) => {
        return this.gridComponentRenderer.renderCellWith(params)
      },
      valueFormatter: (params: Pick<GridValueFormatterParams, 'value'>) => {
        return this.valueFormatterWith(params, precision)
      }
    }
  }

  public generateForecastColDefWith = (field: string, headerName: string, precision: number, width?: number) => {
    return {
      field: field,
      disableColumnMenu: true,
      disableReorder: true,
      editable: true,
      headerName: headerName,
      sortable: false,
      type: 'number',
      width: width || 120,
      renderHeader: (params: GridColumnHeaderParams) => {
        return this.gridComponentRenderer.renderHeaderWith(params)
      },
      renderCell: (params: Pick<GridRenderCellParams, 'row' | 'formattedValue'>) => {
        return this.gridComponentRenderer.renderForecastCellWith(params, field)
      },
      valueFormatter: (params: Pick<GridValueFormatterParams, 'value'>) => {
        return this.valueFormatterWith(params, precision)
      },
      valueGetter: (params: Pick<GridValueGetterParams, 'value'>) =>
        this.gridComponentRenderer.predictionItemValueGetter(params, precision),
      valueSetter: (params: Pick<GridValueSetterParams, 'row' | 'value'>) =>
        this.valueSetterWith(params, field, precision)
    }
  }

  public valueFormatterWith = (params: Pick<GridValueFormatterParams, 'value'>, precision: number) =>
    this.gridComponentRenderer.predictionItemValueFormatter(params, precision)
  public valueGetterWith = (params: Pick<GridValueGetterParams, 'value'>, precision: number) =>
    this.gridComponentRenderer.cellValueGetter(params, precision)
  public predictionitemValueGetterWith = (params: Pick<GridValueGetterParams, 'value'>, precision: number) =>
    this.gridComponentRenderer.predictionItemValueGetter(params, precision)
  public valueSetterWith = (params: Pick<GridValueSetterParams, 'row' | 'value'>, field: string, precision: number) =>
    this.gridComponentRenderer.predictionItemValueSetter(params, field, precision)
}
