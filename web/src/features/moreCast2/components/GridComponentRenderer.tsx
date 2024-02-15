import React from 'react'
import { Box, Button, TextField } from '@mui/material'
import {
  GridColumnHeaderParams,
  GridRenderCellParams,
  GridValueFormatterParams,
  GridValueGetterParams,
  GridValueSetterParams
} from '@mui/x-data-grid'
import { ModelChoice, WeatherDeterminate } from 'api/moreCast2API'
import { createWeatherModelLabel, getDateTimeFromRowID, isPreviousToToday } from 'features/moreCast2/util'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import {
  GC_HEADER,
  PRECIP_HEADER,
  RH_HEADER,
  TEMP_HEADER,
  WIND_DIR_HEADER,
  WIND_SPEED_HEADER
} from 'features/moreCast2/components/ColumnDefBuilder'

export const NOT_AVAILABLE = 'N/A'
export const NOT_REPORTING = 'N/R'

export class GridComponentRenderer {
  public renderForecastHeaderWith = (params: GridColumnHeaderParams) => {
    return <Button>{params.colDef.headerName}</Button>
  }
  public renderHeaderWith = (params: GridColumnHeaderParams) => {
    if (params.field.endsWith('_BIAS')) {
      const headerName = params.colDef.headerName || ''
      const index = headerName.indexOf('_BIAS')
      const prefix = headerName.slice(0, index)
      return (
        <div>
          <Box sx={{ height: '1rem' }}>{prefix}</Box>
          <Box>bias</Box>
        </div>
      )
    }
    return <>{params.colDef.headerName}</>
  }
  public renderCellWith = (params: Pick<GridRenderCellParams, 'formattedValue'>) => (
    <TextField sx={{ pointerEvents: 'none' }} disabled={true} size="small" value={params.formattedValue}></TextField>
  )

  public getActualField = (field: string) => {
    const actualField = field.replace('Forecast', 'Actual')
    return actualField
  }

  public rowContainsActual = (row: MoreCast2Row): boolean => {
    for (const key in row) {
      if (key.includes(WeatherDeterminate.ACTUAL)) {
        const value = row[key as keyof MoreCast2Row]
        if (typeof value === 'number' && !isNaN(value)) {
          return true
        }
      }
    }
    return false
  }

  public valueGetter = (
    params: Pick<GridValueGetterParams, 'row' | 'value'>,
    precision: number,
    field: string
  ): string => {
    if (field.includes('grass')) {
      const actualField = this.getActualField(field)
      const actual = params.row[actualField]

      if (!isNaN(actual)) {
        return Number(actual).toFixed(precision)
      }
    }
    const value = params?.value?.value

    if (isNaN(value)) {
      return 'NaN'
    }
    return Number(value).toFixed(precision)
  }

  public renderForecastCellWith = (params: Pick<GridRenderCellParams, 'row' | 'formattedValue'>, field: string) => {
    // The value of field will be precipForecast, rhForecast, tempForecast, etc.
    // We need the prefix to help us grab the correct 'actual' field (eg. tempACTUAL, precipACTUAL, etc.)
    const actualField = this.getActualField(field)
    const isActual = !isNaN(params.row[actualField])
    const isGrassField = field.includes('grass')
    // We can disable a cell if an Actual exists or the forDate is before today.
    // Both forDate and today are currently in the system's time zone
    const isPreviousDate = isPreviousToToday(params.row['forDate'])

    return (
      <TextField
        disabled={isActual || isPreviousDate}
        size="small"
        label={isGrassField ? '' : createWeatherModelLabel(params.row[field].choice)}
        InputLabelProps={{
          shrink: true
        }}
        value={params.formattedValue}
      ></TextField>
    )
  }

  public predictionItemValueSetter = (
    params: Pick<GridValueSetterParams, 'row' | 'value'>,
    field: string,
    precision: number
  ) => {
    const oldValue = params.row[field].value
    const newValue = params.value ? Number(params.value) : NaN

    if (isNaN(oldValue) && isNaN(newValue)) {
      return { ...params.row }
    }
    // Check if the user has edited the value. If so, update the value and choice to reflect the Manual edit.
    if (newValue.toFixed(precision) !== Number(params.row[field].value).toFixed(precision)) {
      params.row[field].choice = ModelChoice.MANUAL
      params.row[field].value = newValue
    }

    return { ...params.row }
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

  public predictionItemValueFormatter = (
    params: Pick<GridValueFormatterParams, 'field' | 'value' | 'id'>,
    precision: number,
    headerName: string
  ) => {
    const value = Number.parseFloat(params?.value)
    const forDate = getDateTimeFromRowID(params.id!.toString())

    const isForecastColumn = this.isForecastColumn(headerName)
    const isPreviousDate = isPreviousToToday(forDate)

    const noDataField = headerName === WeatherDeterminate.ACTUAL ? NOT_REPORTING : NOT_AVAILABLE

    if (isNaN(value) && isForecastColumn && !isPreviousDate) {
      return ''
    } else return isNaN(value) ? noDataField : value.toFixed(precision)
  }

  public cellValueGetter = (params: Pick<GridValueGetterParams, 'value'>, precision: number) => {
    return isNaN(params?.value) ? 'NaN' : params.value.toFixed(precision)
  }
}
