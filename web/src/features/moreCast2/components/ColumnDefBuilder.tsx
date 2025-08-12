import {
  GridAlignment,
  GridCellParams,
  GridColDef,
  GridColumnHeaderParams,
  GridPreProcessEditCellProps,
  GridRenderCellParams,
  GridRenderEditCellParams,
  GridValueFormatterParams,
  GridValueGetterParams,
  GridValueSetterParams
} from '@mui/x-data-grid-pro'
import { WeatherDeterminate, WeatherDeterminateType } from 'api/moreCast2API'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { DateTime } from 'luxon'
import { Typography, Tooltip, IconButton } from '@mui/material'
import { Info as InfoIcon } from '@mui/icons-material'
import { modelColorClass, modelHeaderColorClass } from 'app/theme'
import { GridComponentRenderer } from 'features/moreCast2/components/GridComponentRenderer'
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

// Helper function to get prediction run timestamp for a weather model
const getPredictionRunTimestamp = (modelType: WeatherDeterminate, allRows: MoreCast2Row[]): string | null => {
  if (!allRows.length) return null

  const timestampField = `predictionRunTimestamp${modelType}` as keyof MoreCast2Row
  const timestamp = allRows[0][timestampField] as string | null | undefined

  return timestamp || null
}

// Helper function to render weather model header with info icon
const renderWeatherModelHeader = (modelType: WeatherDeterminate, allRows?: MoreCast2Row[]) => {
  const timestamp = allRows ? getPredictionRunTimestamp(modelType, allRows) : null
  const displayName = modelType.endsWith('_BIAS') ? `${modelType.replace('_BIAS', '')} bias` : modelType

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
      <Typography style={{ fontWeight: 'bold', fontSize: '12px' }}>{displayName}</Typography>
      {timestamp && (
        <Tooltip title={`Model run: ${DateTime.fromISO(timestamp).toFormat('MMM dd, yyyy HH:mm')} UTC`} arrow>
          <IconButton size="small" style={{ padding: '2px' }}>
            <InfoIcon style={{ fontSize: '14px' }} />
          </IconButton>
        </Tooltip>
      )}
    </div>
  )
}

// Columns that can have values entered as part of a forecast
export const TEMP_HEADER = 'Temp'
export const RH_HEADER = 'RH'
export const WIND_SPEED_HEADER = 'Wind Speed'
export const WIND_DIR_HEADER = 'Wind Dir'
export const PRECIP_HEADER = 'Precip'
export const GC_HEADER = 'GC'

export interface ForecastColDefGenerator {
  getField: () => string
  generateForecastColDef: (
    columnClickHandlerProps: ColumnClickHandlerProps,
    headerName?: string,
    validator?: (value: string) => string
  ) => GridColDef
  generateForecastSummaryColDef: (
    columnClickHandlerProps: ColumnClickHandlerProps,
    validator?: (value: string) => string
  ) => GridColDef
}

export interface ColDefGenerator {
  getField: () => string
  generateColDef: (
    columnClickHandlerProps: ColumnClickHandlerProps,
    headerName?: string,
    validator?: (value: string) => string
  ) => GridColDef
  generateColDefs: (
    columnClickHandlerProps: ColumnClickHandlerProps,
    headerName?: string,
    includeBiasFields?: boolean,
    validator?: (value: string) => string,
    allRows?: MoreCast2Row[]
  ) => GridColDef[]
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
  public generateColDef = () => {
    return this.generateColDefWith(this.field, this.headerName, this.precision, DEFAULT_COLUMN_WIDTH)
  }

  private renderEditCell(params: GridRenderEditCellParams) {
    return <EditInputCell {...params} />
  }

  public generateForecastColDef = (
    columnClickHandlerProps: ColumnClickHandlerProps,
    headerName?: string,
    validator?: (value: string) => string
  ) => {
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
  ) => {
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
  ) => {
    const gridColDefs: GridColDef[] = []
    // Forecast columns have unique requirement (eg. column header menu, editable, etc.)
    const forecastColDef = this.generateForecastColDef(columnClickHandlerProps, headerName, validator)
    gridColDefs.push(forecastColDef)

    for (const colDef of this.generateNonForecastColDefs(includeBiasFields, allRows)) {
      gridColDefs.push(colDef)
    }

    return gridColDefs
  }

  public generateNonForecastColDefs = (includeBiasFields: boolean, allRows?: MoreCast2Row[]) => {
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
  ) => {
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
      renderHeader: (params: GridColumnHeaderParams) => {
        // Check if this is a weather model column that should show tooltip
        const weatherModelsWithTooltips = [
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

        const modelType = weatherModelsWithTooltips.find(model => headerName === model)
        if (modelType && allRows) {
          return renderWeatherModelHeader(modelType, allRows)
        }

        return this.gridComponentRenderer.renderHeaderWith(params)
      },
      valueGetter: (params: Pick<GridValueGetterParams, 'row' | 'value'>) =>
        this.gridComponentRenderer.valueGetter(params, precision, field, headerName),
      valueFormatter: (params: Pick<GridValueFormatterParams, 'value'>) => {
        return this.valueFormatterWith(params, precision)
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
  ) => {
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
      renderHeader: (params: GridColumnHeaderParams) => {
        return isCalcField || isGrassField
          ? this.gridComponentRenderer.renderHeaderWith(params)
          : this.gridComponentRenderer.renderForecastHeaderWith(params, columnClickHandlerProps)
      },
      renderCell: (params: Pick<GridRenderCellParams, 'row' | 'formattedValue' | 'field'>) => {
        return isCalcField
          ? this.gridComponentRenderer.renderCellWith(params)
          : this.gridComponentRenderer.renderForecastCellWith(params, field, validator)
      },
      valueFormatter: (params: Pick<GridValueFormatterParams, 'value'>) => {
        return this.valueFormatterWith(params, precision)
      },
      valueGetter: (params: Pick<GridValueGetterParams, 'row' | 'value'>) =>
        this.gridComponentRenderer.valueGetter(params, precision, field, headerName),
      valueSetter: (params: Pick<GridValueSetterParams, 'row' | 'value'>) =>
        this.valueSetterWith(params, field, precision)
    }
  }

  public generateForecastSummaryColDefWith = (
    field: string,
    headerName: string,
    precision: number,
    columnClickHandlerProps: ColumnClickHandlerProps,
    width?: number,
    validator?: (value: string) => string
  ) => {
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
      renderHeader: (params: GridColumnHeaderParams) => {
        return isCalcField || isGrassField
          ? this.gridComponentRenderer.renderHeaderWith(params)
          : this.gridComponentRenderer.renderForecastHeaderWith(params, columnClickHandlerProps)
      },
      renderCell: (params: Pick<GridRenderCellParams, 'row' | 'formattedValue' | 'field'>) => {
        return isCalcField
          ? this.gridComponentRenderer.renderCellWith(params)
          : this.gridComponentRenderer.renderForecastSummaryCellWith(params)
      },
      valueFormatter: (params: Pick<GridValueFormatterParams, 'value'>) => {
        return this.valueFormatterWith(params, precision)
      },
      valueGetter: (params: Pick<GridValueGetterParams, 'row' | 'value'>) =>
        this.gridComponentRenderer.valueGetter(params, precision, field, headerName),
      valueSetter: (params: Pick<GridValueSetterParams, 'row' | 'value'>) =>
        this.valueSetterWith(params, field, precision)
    }
  }

  public valueFormatterWith = (params: Pick<GridValueFormatterParams, 'value'>, precision: number) =>
    this.gridComponentRenderer.predictionItemValueFormatter(params, precision)
  public valueGetter = (
    params: Pick<GridValueGetterParams, 'row' | 'value'>,
    field: string,
    precision: number,
    headerName: string
  ) => this.gridComponentRenderer.valueGetter(params, precision, field, headerName)
  public valueSetterWith = (params: Pick<GridValueSetterParams, 'row' | 'value'>, field: string, precision: number) =>
    this.gridComponentRenderer.predictionItemValueSetter(params, field, precision)
}
