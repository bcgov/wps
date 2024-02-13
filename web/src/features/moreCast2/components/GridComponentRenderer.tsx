import React from 'react'
import { Box, Button, TextField } from '@mui/material'
import {
  GridColumnHeaderParams,
  GridRenderCellParams,
  GridValueFormatterParams,
  GridValueGetterParams,
  GridValueSetterParams
} from '@mui/x-data-grid'
import { ModelChoice } from 'api/moreCast2API'
import { createWeatherModelLabel } from 'features/moreCast2/util'
import { DateTime } from 'luxon'

const NOT_AVAILABLE = 'N/A'

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
    const isPreviousDate = params.row['forDate'] < DateTime.now()

    const isGrassField = field.includes('grass')

    return (
      <TextField
        disabled={isActual || isPreviousDate}
        size="small"
        label={isGrassField ? '' : createWeatherModelLabel(params.row[field].choice)}
        InputLabelProps={{
          shrink: true
        }}
        value={!isActual && params.formattedValue === NOT_AVAILABLE && !isPreviousDate ? '' : params.formattedValue}
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

  public predictionItemValueFormatter = (params: Pick<GridValueFormatterParams, 'value'>, precision: number) => {
    const value = Number.parseFloat(params?.value)

    return isNaN(value) ? NOT_AVAILABLE : value.toFixed(precision)
  }

  public cellValueGetter = (params: Pick<GridValueGetterParams, 'value'>, precision: number) => {
    return isNaN(params?.value) ? 'NaN' : params.value.toFixed(precision)
  }
}
