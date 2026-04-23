import { TextField, Typography } from '@mui/material'
import { GridColumnHeaderParams, GridRenderCellParams } from '@mui/x-data-grid-pro'
import { ModelChoice, WeatherDeterminate } from '@wps/api/moreCast2API'
import { createWeatherModelLabel, isBeforeToday, isForecastRow, rowContainsActual } from 'features/moreCast2/util'
import {
  GC_HEADER,
  PRECIP_HEADER,
  RH_HEADER,
  TEMP_HEADER,
  WIND_DIR_HEADER,
  WIND_SPEED_HEADER
} from 'features/moreCast2/components/ColumnDefBuilder'
import { theme } from '@wps/ui/theme'
import ForecastHeader from 'features/moreCast2/components/ForecastHeader'
import { ColumnClickHandlerProps } from 'features/moreCast2/components/TabbedDataGrid'
import { isNumber } from 'lodash'
import ForecastCell from 'features/moreCast2/components/ForecastCell'
import ValidatedGrassCureForecastCell from '@/features/moreCast2/components/ValidatedGrassCureForecastCell'
import ValidatedWindDirectionForecastCell from '@/features/moreCast2/components/ValidatedWindDirectionForecastCell'
import ActualCell from 'features/moreCast2/components/ActualCell'
import { MoreCast2Row, PredictionItem } from '@/features/moreCast2/interfaces'
import ModelHeader from '@/features/moreCast2/components/ModelHeader'

export const NOT_AVAILABLE = 'N/A'
export const NOT_REPORTING = 'N/R'

export type GridRendererValue = number | string | PredictionItem | null | undefined
export type GridRendererEditableValue = number | string | null | undefined

export class GridComponentRenderer {
  private getRowValue = (row: MoreCast2Row, field: string) => row[field as keyof MoreCast2Row]

  private isPredictionItem = (value: unknown): value is PredictionItem => {
    return value != null && typeof value === 'object' && 'choice' in value && 'value' in value
  }

  private getPredictionItem = (row: MoreCast2Row, field: string): PredictionItem | undefined => {
    const fieldValue = this.getRowValue(row, field)

    return this.isPredictionItem(fieldValue) ? fieldValue : undefined
  }

  private getNumericValue = (row: MoreCast2Row, field: string): number | undefined => {
    const fieldValue = this.getRowValue(row, field)

    return typeof fieldValue === 'number' ? fieldValue : undefined
  }

  private unwrapPredictionValue = (value: GridRendererValue): number | string | null | undefined => {
    return this.isPredictionItem(value) ? value.value : value
  }

  public renderForecastHeaderWith = (
    params: GridColumnHeaderParams<MoreCast2Row>,
    columnClickHandlerProps: ColumnClickHandlerProps
  ) => {
    return <ForecastHeader colDef={params.colDef} columnClickHandlerProps={columnClickHandlerProps} />
  }
  public renderHeaderWith = (
    params: Pick<GridColumnHeaderParams<MoreCast2Row>, 'field'> & {
      colDef: Pick<GridColumnHeaderParams<MoreCast2Row>['colDef'], 'field' | 'headerName'>
    },
    allRows?: MoreCast2Row[]
  ) => {
    const headerName = params.colDef.headerName ?? ''

    if (params.field.endsWith('_BIAS')) {
      const index = headerName.indexOf('_BIAS')
      const prefix = headerName.slice(0, index)
      return (
        <div data-testid={`${params.colDef.field}-column-header`}>
          <Typography data-testid={`${params.colDef.field}-column-header`} style={{ fontSize: '14px' }}>
            {prefix}
          </Typography>
          <Typography style={{ fontSize: '14px' }}>bias</Typography>
        </div>
      )
    }
    return <ModelHeader params={params} allRows={allRows} />
  }

  public renderCellWith = (params: Pick<GridRenderCellParams, 'formattedValue' | 'field' | 'row'>) => {
    if (!isForecastRow(params.row) && params.field.endsWith('Actual')) {
      return <ActualCell missingActual={params.formattedValue === NOT_REPORTING} value={params.formattedValue} />
    }
    return (
      <TextField
        sx={{ pointerEvents: 'none', backgroundColor: theme.palette.common.white, borderRadius: 1 }}
        disabled={true}
        size="small"
        value={params.formattedValue}
      ></TextField>
    )
  }

  public getActualField = (field: string) => {
    const actualField = field.replace('Forecast', 'Actual')
    return actualField
  }

  public valueGetter = (
    value: GridRendererValue,
    row: MoreCast2Row,
    precision: number,
    field: string,
    headerName: string
  ): string => {
    // The grass curing and calculated fwi indices show both actuals and forecasts in the same column
    if (field.includes('grass') || field.includes('Calc')) {
      const actualField = this.getActualField(field)
      const actual = this.getNumericValue(row, actualField)

      if (actual !== undefined && !isNaN(actual)) {
        return actual.toFixed(precision)
      }
    }

    const resolvedValue = this.unwrapPredictionValue(value)
    // The 'Actual' column will show N/R for Not Reporting, instead of N/A
    const noDataField = headerName === WeatherDeterminate.ACTUAL ? NOT_REPORTING : NOT_AVAILABLE

    const isPreviousDate = isBeforeToday(row.forDate)
    const isForecastColumn = this.isForecastColumn(headerName)
    const containsActual = rowContainsActual(row)

    const isBlankForecastCell = !isPreviousDate && isForecastColumn && !containsActual

    // Treat null as missing data, not as 0
    if (resolvedValue == null) {
      return isBlankForecastCell ? '' : noDataField
    }

    const numericValue = Number(resolvedValue)

    // If a cell has no value, belongs to a Forecast column, is a future forDate, and the row doesn't contain any Actuals from today,
    // we can leave it blank, so it's obvious that it can have a value entered into it.
    if (Number.isNaN(numericValue) && isBlankForecastCell) {
      return ''
    }

    return Number.isNaN(numericValue) ? noDataField : numericValue.toFixed(precision)
  }

  public renderForecastCellWith = (
    params: Pick<GridRenderCellParams, 'row' | 'formattedValue'>,
    field: string,
    validator?: (value: string) => string
  ) => {
    // If a single cell in a row contains an Actual, no Forecast will be entered into the row anymore, so we can disable the whole row.
    const isActual = rowContainsActual(params.row)
    // We can disable a cell if an Actual exists or the forDate is before today.
    // Both forDate and today are currently in the system's time zone
    const isPreviousDate = isBeforeToday(params.row.forDate)
    const isGrassField = field.includes('grass')
    const forecastValue = this.getPredictionItem(params.row, field)
    const label =
      isGrassField || isPreviousDate ? '' : createWeatherModelLabel(forecastValue?.choice ?? ModelChoice.NULL)
    const formattedValue = parseFloat(params.formattedValue)
    const actualField = this.getActualField(field)
    const actualValue = this.getNumericValue(params.row, actualField)
    let showLessThan = false
    let showGreaterThan = false
    // Only show + and - icons if an actual value exists, a forecast value exists and this is not a windDirection
    // field.
    if (
      actualValue !== undefined &&
      !isNaN(actualValue) &&
      isNumber(actualValue) &&
      isNumber(formattedValue) &&
      !field.includes('windDirection')
    ) {
      showLessThan = formattedValue < actualValue
      showGreaterThan = formattedValue > actualValue
    }

    // The grass curing 'forecast' field is rendered differently
    if (isGrassField) {
      return (
        <ValidatedGrassCureForecastCell
          disabled={isActual || isPreviousDate}
          label={label}
          value={params.formattedValue}
          validator={validator}
        />
      )
    } else if (field.includes('windDirection')) {
      return (
        <ValidatedWindDirectionForecastCell
          disabled={isActual || isPreviousDate}
          label={label}
          value={params.formattedValue}
          validator={validator}
        />
      )
    } else {
      // Forecast fields (except wind direction) have plus and minus icons indicating if the forecast was
      // greater than or less than the actual
      return (
        <ForecastCell
          disabled={isActual || isPreviousDate}
          label={label}
          showGreaterThan={showGreaterThan}
          showLessThan={showLessThan}
          value={params.formattedValue}
          validator={validator}
        />
      )
    }
  }

  public renderForecastSummaryCellWith = (params: Pick<GridRenderCellParams, 'row' | 'formattedValue'>) => {
    // If a single cell in a row contains an Actual, no Forecast will be entered into the row anymore, so we can disable the whole row.
    const isActual = rowContainsActual(params.row)
    // We can disable a cell if an Actual exists or the forDate is before today.
    // Both forDate and today are currently in the system's time zone
    const isPreviousDate = isBeforeToday(params.row.forDate)

    // The grass curing 'forecast' field and other weather parameter forecasts fields are rendered differently
    return <TextField disabled={isActual || isPreviousDate} size="small" value={params.formattedValue}></TextField>
  }

  public predictionItemValueSetter = (
    value: GridRendererEditableValue,
    row: MoreCast2Row,
    field: string,
    precision: number
  ): MoreCast2Row => {
    const predictionItem = this.getPredictionItem(row, field)

    if (!predictionItem) {
      return row
    }

    const oldValue = predictionItem.value
    const newValue = isNaN(Number(value)) ? NaN : Number(value)

    if (isNaN(oldValue) && isNaN(newValue)) {
      return row
    }

    if (newValue.toFixed(precision) === oldValue.toFixed(precision)) {
      return row
    }

    const fixedValue = newValue.toFixed(precision)

    return {
      ...row,
      [field]: {
        ...predictionItem,
        choice: ModelChoice.MANUAL,
        value: precision === 0 ? parseInt(fixedValue, 10) : parseFloat(fixedValue)
      }
    } as MoreCast2Row
  }

  public isForecastColumn = (headerName: string): boolean => {
    const forecastColumns = [
      WeatherDeterminate.FORECAST,
      TEMP_HEADER,
      RH_HEADER,
      WIND_DIR_HEADER,
      WIND_SPEED_HEADER,
      PRECIP_HEADER,
      GC_HEADER
    ]

    return forecastColumns.some(column => column === headerName)
  }

  public predictionItemValueFormatter = (value: GridRendererValue, precision: number) => {
    const parsedValue = Number.parseFloat(String(value))

    return isNaN(parsedValue) ? value : parsedValue.toFixed(precision)
  }
}
