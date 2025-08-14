import React from 'react'
import { Box, IconButton, TextField, Tooltip, Typography } from '@mui/material'
import {
  GridColumnHeaderParams,
  GridRenderCellParams,
  GridValueFormatterParams,
  GridValueGetterParams,
  GridValueSetterParams
} from '@mui/x-data-grid-pro'
import { Info as InfoIcon } from '@mui/icons-material'
import { ModelChoice, WeatherDeterminate, weatherModelsWithTooltips } from 'api/moreCast2API'
import { createWeatherModelLabel, isBeforeToday, isForecastRow, rowContainsActual } from 'features/moreCast2/util'
import {
  GC_HEADER,
  PRECIP_HEADER,
  RH_HEADER,
  TEMP_HEADER,
  WIND_DIR_HEADER,
  WIND_SPEED_HEADER
} from 'features/moreCast2/components/ColumnDefBuilder'
import { theme } from 'app/theme'
import ForecastHeader from 'features/moreCast2/components/ForecastHeader'
import { ColumnClickHandlerProps } from 'features/moreCast2/components/TabbedDataGrid'
import { cloneDeep, isNumber } from 'lodash'
import ForecastCell from 'features/moreCast2/components/ForecastCell'
import ValidatedGrassCureForecastCell from '@/features/moreCast2/components/ValidatedGrassCureForecastCell'
import ValidatedWindDirectionForecastCell from '@/features/moreCast2/components/ValidatedWindDirectionForecastCell'
import ActualCell from 'features/moreCast2/components/ActualCell'
import { MoreCast2Row } from '@/features/moreCast2/interfaces'
import { DateTime } from 'luxon'

export const NOT_AVAILABLE = 'N/A'
export const NOT_REPORTING = 'N/R'

export class GridComponentRenderer {
  public renderForecastHeaderWith = (
    params: GridColumnHeaderParams,
    columnClickHandlerProps: ColumnClickHandlerProps
  ) => {
    return <ForecastHeader colDef={params.colDef} columnClickHandlerProps={columnClickHandlerProps} />
  }
  public renderHeaderWith = (params: GridColumnHeaderParams, allRows?: MoreCast2Row[]) => {
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
    const modelType = weatherModelsWithTooltips.find(model => headerName === model)
    if (modelType && allRows && allRows.length > 0) {
      const timestampField = `predictionRunTimestamp${modelType}` as keyof MoreCast2Row
      const timestamp = allRows[0][timestampField] as string | null | undefined
      return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Typography style={{ fontSize: '14px' }}>{headerName}</Typography>
          {timestamp && (
            <Tooltip title={`Model run: ${DateTime.fromISO(timestamp).toFormat('MMM dd, yyyy HH:mm ZZZZ')}`} arrow>
              <IconButton size="small" style={{ padding: '2px' }}>
                <InfoIcon style={{ fontSize: '14px' }} />
              </IconButton>
            </Tooltip>
          )}
        </div>
      )
    }
    return (
      <Typography data-testid={`${params.colDef.field}-column-header`} style={{ fontSize: '14px' }}>
        {headerName}
      </Typography>
    )
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
    params: Pick<GridValueGetterParams, 'row' | 'value'>,
    precision: number,
    field: string,
    headerName: string
  ): string => {
    // The grass curing and calculated fwi indices show both actuals and forecasts in the same column
    if (field.includes('grass') || field.includes('Calc')) {
      const actualField = this.getActualField(field)
      const actual = params.row[actualField]

      if (!isNaN(actual)) {
        return Number(actual).toFixed(precision)
      }
    }

    const value = params?.value?.value ?? params.value
    // The 'Actual' column will show N/R for Not Reporting, instead of N/A
    const noDataField = headerName === WeatherDeterminate.ACTUAL ? NOT_REPORTING : NOT_AVAILABLE

    const isPreviousDate = isBeforeToday(params.row['forDate'])
    const isForecastColumn = this.isForecastColumn(headerName)
    const containsActual = rowContainsActual(params.row)

    // If a cell has no value, belongs to a Forecast column, is a future forDate, and the row doesn't contain any Actuals from today,
    // we can leave it blank, so it's obvious that it can have a value entered into it.
    if (isNaN(value) && !isPreviousDate && isForecastColumn && !containsActual) {
      return ''
    } else return isNaN(value) ? noDataField : Number(value).toFixed(precision)
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
    const isPreviousDate = isBeforeToday(params.row['forDate'])
    const isGrassField = field.includes('grass')
    const label = isGrassField || isPreviousDate ? '' : createWeatherModelLabel(params.row[field].choice)
    const formattedValue = parseFloat(params.formattedValue)
    const actualField = this.getActualField(field)
    const actualValue = params.row[actualField]
    let showLessThan = false
    let showGreaterThan = false
    // Only show + and - icons if an actual value exists, a forecast value exists and this is not a windDirection
    // field.
    if (!isNaN(actualValue) && isNumber(actualValue) && isNumber(formattedValue) && !field.includes('windDirection')) {
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
    const isPreviousDate = isBeforeToday(params.row['forDate'])

    // The grass curing 'forecast' field and other weather parameter forecasts fields are rendered differently
    return <TextField disabled={isActual || isPreviousDate} size="small" value={params.formattedValue}></TextField>
  }

  public predictionItemValueSetter = (
    params: Pick<GridValueSetterParams, 'row' | 'value'>,
    field: string,
    precision: number
  ) => {
    const oldValue = params.row[field].value
    const newValue = isNaN(params.value) ? NaN : Number(params.value)

    if (isNaN(oldValue) && isNaN(newValue)) {
      return { ...params.row }
    }
    // Check if the user has edited the value. If so, update the value and choice to reflect the Manual edit.
    if (newValue.toFixed(precision) !== Number(params.row[field].value).toFixed(precision)) {
      params.row[field].choice = ModelChoice.MANUAL
      const fixedValue = newValue.toFixed(precision)

      params.row[field].value = precision === 0 ? parseInt(fixedValue) : parseFloat(fixedValue)
    }

    return cloneDeep(params.row)
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

  public predictionItemValueFormatter = (params: Pick<GridValueFormatterParams, 'value'>, precision: number) => {
    const value = Number.parseFloat(params?.value)

    return isNaN(value) ? params.value : value.toFixed(precision)
  }
}
