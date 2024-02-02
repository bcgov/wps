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
export const DEFAULT_FORECAST_COLUMN_WIDTH = 120

// Defines the order in which weather models display in the datagrid.
export const ORDERED_COLUMN_HEADERS: WeatherDeterminateType[] = [
  WeatherDeterminate.HRDPS,
  WeatherDeterminate.HRDPS_BIAS,
  WeatherDeterminate.RDPS,
  WeatherDeterminate.RDPS_BIAS,
  WeatherDeterminate.GDPS,
  WeatherDeterminate.GDPS_BIAS,
  WeatherDeterminate.NAM,
  WeatherDeterminate.NAM_BIAS,
  WeatherDeterminate.GFS,
  WeatherDeterminate.GFS_BIAS
]

export interface ForecastColDefGenerator {
  generateForecastColDef: (headerName?: string) => GridColDef
}

export interface ColDefGenerator {
  generateColDef: (headerName?: string) => GridColDef
  generateColDefs: (headerName?: string, includeBiasFields?: boolean) => GridColDef[]
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
      DEFAULT_FORECAST_COLUMN_WIDTH
    )
  }

  public generateColDefs = (headerName?: string, includeBiasFields = true) => {
    const gridColDefs: GridColDef[] = []
    // Forecast columns have unique requirement (eg. column header menu, editable, etc.)
    const forecastColDef = this.generateForecastColDef(headerName)
    gridColDefs.push(forecastColDef)

    for (const colDef of this.generateNonForecastColDefs(includeBiasFields)) {
      gridColDefs.push(colDef)
    }

    return gridColDefs
  }

  public generateNonForecastColDefs = (includeBiasFields: boolean) => {
    const fields = includeBiasFields
      ? ORDERED_COLUMN_HEADERS
      : ORDERED_COLUMN_HEADERS.filter(header => !header.endsWith('_BIAS'))
    return fields.map(header =>
      this.generateColDefWith(`${this.field}${header}`, header, this.precision, DEFAULT_COLUMN_WIDTH)
    )
  }

  public generateColDefWith = (field: string, headerName: string, precision: number, width?: number) => {
    return {
      field,
      disableColumnMenu: true,
      disableReorder: true,
      headerName,
      sortable: false,
      type: 'number',
      width: width ? width : DEFAULT_COLUMN_WIDTH,
      renderCell: (params: Pick<GridRenderCellParams, 'formattedValue'>) => {
        return this.gridComponentRenderer.renderCellWith(params)
      },
      renderHeader: (params: GridColumnHeaderParams) => {
        return this.gridComponentRenderer.renderHeaderWith(params)
      },
      valueFormatter: (params: Pick<GridValueFormatterParams, 'value'>) => {
        return this.valueFormatterWith(params, precision)
      }
    }
  }

  public generateForecastColDefWith = (field: string, headerName: string, precision: number, width?: number) => {
    const isGrassField = field.includes('grass')
    const isCalcField = field.includes('Calc')
    if (isGrassField || isCalcField) {
      width = DEFAULT_COLUMN_WIDTH
    }
    return {
      field: field,
      disableColumnMenu: true,
      disableReorder: true,
      editable: true,
      headerName: headerName,
      sortable: false,
      type: 'number',
      width: width || DEFAULT_FORECAST_COLUMN_WIDTH,
      renderHeader: (params: GridColumnHeaderParams) => {
        return isCalcField || isGrassField
          ? this.gridComponentRenderer.renderHeaderWith(params)
          : this.gridComponentRenderer.renderForecastHeaderWith(params)
      },
      renderCell: (params: Pick<GridRenderCellParams, 'row' | 'formattedValue'>) => {
        return isCalcField
          ? this.gridComponentRenderer.renderCellWith(params)
          : this.gridComponentRenderer.renderForecastCellWith(params, field)
      },
      valueFormatter: (params: Pick<GridValueFormatterParams, 'value'>) => {
        return this.valueFormatterWith(params, precision)
      },
      valueGetter: (params: Pick<GridValueGetterParams, 'row' | 'value'>) =>
        this.gridComponentRenderer.valueGetter(params, precision, field),
      valueSetter: (params: Pick<GridValueSetterParams, 'row' | 'value'>) =>
        this.valueSetterWith(params, field, precision)
    }
  }

  public valueFormatterWith = (params: Pick<GridValueFormatterParams, 'value'>, precision: number) =>
    this.gridComponentRenderer.predictionItemValueFormatter(params, precision)
  public valueGetterWith = (params: Pick<GridValueGetterParams, 'value'>, precision: number) =>
    this.gridComponentRenderer.cellValueGetter(params, precision)
  public valueGetter = (params: Pick<GridValueGetterParams, 'row' | 'value'>, field: string, precision: number) =>
    this.gridComponentRenderer.valueGetter(params, precision, field)
  public valueSetterWith = (params: Pick<GridValueSetterParams, 'row' | 'value'>, field: string, precision: number) =>
    this.gridComponentRenderer.predictionItemValueSetter(params, field, precision)
}
