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

    // Actual and model prediction columns only show data, so require a simple column definition
    for (const determinate of ORDERED_COLUMN_HEADERS) {
      const fieldName = `${this.field}${determinate}`
      const gridColDef = this.generateColDefWith(fieldName, determinate, this.precision, DEFAULT_COLUMN_WIDTH)
      gridColDefs.push(gridColDef)
    }
    return gridColDefs
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
      renderCell: (params: GridRenderCellParams) => {
        return this.gridComponentRenderer.renderCellWith(params)
      },
      valueFormatter: (params: GridValueFormatterParams) => {
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
      renderCell: (params: GridRenderCellParams) => {
        return this.gridComponentRenderer.renderForecastCellWith(params, field)
      },
      valueFormatter: (params: GridValueFormatterParams) => {
        return this.valueFormatterWith(params, precision)
      },
      valueGetter: (params: GridValueGetterParams) =>
        this.gridComponentRenderer.predictionItemValueGetter(params, precision),
      valueSetter: (params: GridValueSetterParams) => this.valueSetterWith(params, field, precision)
    }
  }

  protected valueFormatterWith = (params: GridValueFormatterParams, precision: number) =>
    this.gridComponentRenderer.predictionItemValueFormatter(params, precision)
  protected valueGetterWith = (params: GridValueGetterParams, precision: number) =>
    this.gridComponentRenderer.cellValueGetter(params, precision)
  protected predictionitemValueGetterWith = (params: GridValueGetterParams, precision: number) =>
    this.gridComponentRenderer.predictionItemValueGetter(params, precision)
  protected valueSetterWith = (params: GridValueSetterParams, field: string, precision: number) =>
    this.gridComponentRenderer.predictionItemValueSetter(params, field, precision)
}
