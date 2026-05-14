import {
  GridAlignment,
  GridCellParams,
  GridColDef,
  GridColumnHeaderParams,
  GridPreProcessEditCellProps,
  GridRenderCellParams,
  GridRenderEditCellParams
} from '@mui/x-data-grid-pro'
import { WeatherDeterminate, WeatherDeterminateType } from '@wps/api/moreCast2API'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { modelColorClass, modelHeaderColorClass } from '@wps/ui/theme'
import {
  GridComponentRenderer,
  GridRendererEditableValue,
  GridRendererValue
} from 'features/moreCast2/components/GridComponentRenderer'
import { ColumnClickHandlerProps } from 'features/moreCast2/components/TabbedDataGrid'
import { EditInputCell } from '@/features/moreCast2/components/EditInputCell'

export const DEFAULT_COLUMN_WIDTH = 80
export const DEFAULT_FORECAST_COLUMN_WIDTH = 145
export const DEFAULT_FORECAST_SUMMARY_COLUMN_WIDTH = 110

// Defines the order in which weather models display in the datagrid.
export const ORDERED_COLUMN_HEADERS: WeatherDeterminateType[] = [
  WeatherDeterminate.ACTUAL,
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

export const PINNED_COLUMNS = ['stationName', 'forDate']

// Columns that can have values entered as part of a forecast
export const TEMP_HEADER = 'Temp'
export const RH_HEADER = 'RH'
export const WIND_SPEED_HEADER = 'Wind Speed'
export const WIND_DIR_HEADER = 'Wind Dir'
export const PRECIP_HEADER = 'Precip'
export const GC_HEADER = 'GC'

export type MoreCast2GridColDef = GridColDef<MoreCast2Row>

export interface ForecastColDefGenerator {
  getField: () => string
  generateForecastColDef: (
    columnClickHandlerProps: ColumnClickHandlerProps,
    headerName?: string,
    validator?: (value: string) => string
  ) => MoreCast2GridColDef
  generateForecastSummaryColDef: (
    columnClickHandlerProps: ColumnClickHandlerProps,
    validator?: (value: string) => string
  ) => MoreCast2GridColDef
}

export interface ColDefGenerator {
  getField: () => string
  generateColDef: (
    columnClickHandlerProps: ColumnClickHandlerProps,
    headerName?: string,
    validator?: (value: string) => string
  ) => MoreCast2GridColDef
  generateColDefs: (
    columnClickHandlerProps: ColumnClickHandlerProps,
    headerName?: string,
    includeBiasFields?: boolean,
    validator?: (value: string) => string,
    allRows?: MoreCast2Row[]
  ) => MoreCast2GridColDef[]
}

export class ColumnDefBuilder implements ColDefGenerator, ForecastColDefGenerator {
  constructor(
    readonly field: string,
    readonly headerName: string,
    readonly type: 'string' | 'number',
    readonly precision: number,
    readonly gridComponentRenderer: GridComponentRenderer
  ) {}
  public getField = () => {
    return this.field
  }
  public generateColDef = (): MoreCast2GridColDef => {
    return this.generateColDefWith(this.field, this.headerName, this.precision, DEFAULT_COLUMN_WIDTH)
  }

  private renderEditCell(params: GridRenderEditCellParams) {
    return <EditInputCell {...params} />
  }

  public generateForecastColDef = (
    columnClickHandlerProps: ColumnClickHandlerProps,
    headerName?: string,
    validator?: (value: string) => string
  ): MoreCast2GridColDef => {
    return this.generateForecastColDefWith(
      `${this.field}${WeatherDeterminate.FORECAST}`,
      headerName ?? this.headerName,
      this.precision,
      columnClickHandlerProps,
      DEFAULT_FORECAST_COLUMN_WIDTH,
      validator
    )
  }

  public generateForecastSummaryColDef = (
    columnClickHandlerProps: ColumnClickHandlerProps,
    validator?: (value: string) => string
  ): MoreCast2GridColDef => {
    return this.generateForecastSummaryColDefWith(
      `${this.field}${WeatherDeterminate.FORECAST}`,
      this.headerName,
      this.precision,
      columnClickHandlerProps,
      DEFAULT_FORECAST_SUMMARY_COLUMN_WIDTH,
      validator
    )
  }

  public generateColDefs = (
    columnClickHandlerProps: ColumnClickHandlerProps,
    headerName?: string,
    includeBiasFields = true,
    validator?: (value: string) => string,
    allRows?: MoreCast2Row[]
  ): MoreCast2GridColDef[] => {
    const gridColDefs: MoreCast2GridColDef[] = []
    // Forecast columns have unique requirement (eg. column header menu, editable, etc.)
    const forecastColDef = this.generateForecastColDef(columnClickHandlerProps, headerName, validator)
    gridColDefs.push(forecastColDef)

    for (const colDef of this.generateNonForecastColDefs(includeBiasFields, allRows)) {
      gridColDefs.push(colDef)
    }

    return gridColDefs
  }

  public generateNonForecastColDefs = (includeBiasFields: boolean, allRows?: MoreCast2Row[]): MoreCast2GridColDef[] => {
    const fields = includeBiasFields
      ? ORDERED_COLUMN_HEADERS
      : ORDERED_COLUMN_HEADERS.filter(header => !header.endsWith('_BIAS'))
    return fields.map(header =>
      this.generateColDefWith(
        `${this.field}${header}`,
        header,
        this.precision,
        DEFAULT_COLUMN_WIDTH,
        undefined,
        allRows
      )
    )
  }

  public generateColDefWith = (
    field: string,
    headerName: string,
    precision: number,
    width?: number,
    validator?: (value: string) => string,
    allRows?: MoreCast2Row[]
  ): MoreCast2GridColDef => {
    return {
      field,
      disableColumnMenu: true,
      disableReorder: true,
      headerAlign: 'center' as GridAlignment,
      headerName,
      sortable: false,
      type: 'number',
      width: width ?? DEFAULT_COLUMN_WIDTH,
      renderEditCell: this.renderEditCell,
      preProcessEditCellProps: (params: GridPreProcessEditCellProps) => {
        return { ...params.props, error: validator ? validator(params.props.value) : '' }
      },
      cellClassName: (params: Pick<GridCellParams, 'colDef' | 'field'>) => {
        return modelColorClass(params)
      },
      headerClassName: (params: Pick<GridColumnHeaderParams, 'colDef' | 'field'>) => {
        return modelHeaderColorClass(params)
      },
      renderCell: (params: Pick<GridRenderCellParams, 'formattedValue' | 'field' | 'row'>) => {
        return this.gridComponentRenderer.renderCellWith(params)
      },
      renderHeader: (params: GridColumnHeaderParams<MoreCast2Row>) => {
        return this.gridComponentRenderer.renderHeaderWith(params, allRows)
      },
      valueGetter: (value: GridRendererValue, row: MoreCast2Row) =>
        this.gridComponentRenderer.valueGetter(value, row, precision, field, headerName),
      valueFormatter: (value: GridRendererValue) => {
        return this.valueFormatterWith(value, precision)
      }
    }
  }

  public generateForecastColDefWith = (
    field: string,
    headerName: string,
    precision: number,
    columnClickHandlerProps: ColumnClickHandlerProps,
    width?: number,
    validator?: (value: string) => string
  ): MoreCast2GridColDef => {
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
      headerAlign: 'center' as GridAlignment,
      headerName: headerName,
      sortable: false,
      type: 'number',
      width: width ?? DEFAULT_FORECAST_COLUMN_WIDTH,
      renderEditCell: this.renderEditCell,
      preProcessEditCellProps: (params: GridPreProcessEditCellProps) => {
        return { ...params.props, error: validator ? validator(params.props.value) : '' }
      },
      renderHeader: (params: GridColumnHeaderParams<MoreCast2Row>) => {
        return isCalcField || isGrassField
          ? this.gridComponentRenderer.renderHeaderWith(params)
          : this.gridComponentRenderer.renderForecastHeaderWith(params, columnClickHandlerProps)
      },
      renderCell: (params: Pick<GridRenderCellParams, 'row' | 'formattedValue' | 'field'>) => {
        return isCalcField
          ? this.gridComponentRenderer.renderCellWith(params)
          : this.gridComponentRenderer.renderForecastCellWith(params, field, validator)
      },
      valueFormatter: (value: GridRendererValue) => {
        return this.valueFormatterWith(value, precision)
      },
      valueGetter: (value: GridRendererValue, row: MoreCast2Row) =>
        this.gridComponentRenderer.valueGetter(value, row, precision, field, headerName),
      valueSetter: (value: GridRendererEditableValue, row: MoreCast2Row) =>
        this.valueSetterWith(value, row, field, precision)
    }
  }

  public generateForecastSummaryColDefWith = (
    field: string,
    headerName: string,
    precision: number,
    columnClickHandlerProps: ColumnClickHandlerProps,
    width?: number,
    validator?: (value: string) => string
  ): MoreCast2GridColDef => {
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
      headerAlign: 'center' as GridAlignment,
      headerName: headerName,
      sortable: false,
      type: 'number',
      width: width ?? DEFAULT_FORECAST_SUMMARY_COLUMN_WIDTH,
      preProcessEditCellProps: (params: GridPreProcessEditCellProps) => {
        return { ...params.props, error: validator ? validator(params.props.value) : '' }
      },
      renderEditCell: this.renderEditCell,
      renderHeader: (params: GridColumnHeaderParams<MoreCast2Row>) => {
        return isCalcField || isGrassField
          ? this.gridComponentRenderer.renderHeaderWith(params)
          : this.gridComponentRenderer.renderForecastHeaderWith(params, columnClickHandlerProps)
      },
      renderCell: (params: Pick<GridRenderCellParams, 'row' | 'formattedValue' | 'field'>) => {
        return isCalcField
          ? this.gridComponentRenderer.renderCellWith(params)
          : this.gridComponentRenderer.renderForecastSummaryCellWith(params)
      },
      valueFormatter: (value: GridRendererValue) => {
        return this.valueFormatterWith(value, precision)
      },
      valueGetter: (value: GridRendererValue, row: MoreCast2Row) =>
        this.gridComponentRenderer.valueGetter(value, row, precision, field, headerName),
      valueSetter: (value: GridRendererEditableValue, row: MoreCast2Row) =>
        this.valueSetterWith(value, row, field, precision)
    }
  }

  public valueFormatterWith = (value: GridRendererValue, precision: number) =>
    this.gridComponentRenderer.predictionItemValueFormatter(value, precision)
  public valueGetter = (
    value: GridRendererValue,
    row: MoreCast2Row,
    field: string,
    precision: number,
    headerName: string
  ) => this.gridComponentRenderer.valueGetter(value, row, precision, field, headerName)
  public valueSetterWith = (value: GridRendererEditableValue, row: MoreCast2Row, field: string, precision: number) =>
    this.gridComponentRenderer.predictionItemValueSetter(value, row, field, precision)
}
