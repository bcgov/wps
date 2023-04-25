import React from 'react'
import { Button, TextField } from '@mui/material'
import {
  GridColumnHeaderParams,
  GridRenderCellParams,
  GridValueFormatterParams,
  GridValueGetterParams,
  GridValueSetterParams
} from '@mui/x-data-grid'
import { ModelChoice } from 'api/moreCast2API'

const NOT_AVAILABLE = 'N/A'

export class GridComponentRenderer {
  public renderHeaderWith = (params: GridColumnHeaderParams) => {
    return <Button>{params.colDef.headerName}</Button>
  }
  public renderCellWith = (params: Pick<GridRenderCellParams, 'formattedValue'>) => (
    <TextField disabled={true} size="small" value={params.formattedValue}></TextField>
  )

  public renderForecastCellWith = (
    params: Pick<GridRenderCellParams, 'row' | 'formattedValue'>,
    field: string,
    editMode: boolean
  ) => {
    // The value of field will be precipForecast, rhForecast, tempForecast, etc.
    // We need the prefix to help us grab the correct 'actual' field (eg. tempACTUAL, precipACTUAL, etc.)
    const index = field.indexOf('Forecast')
    const prefix = field.slice(0, index)
    const actualField = `${prefix}Actual`

    const disabled = !isNaN(params.row[actualField]) || editMode
    return (
      <TextField
        disabled={disabled}
        size="small"
        label={params.row[field].choice}
        value={params.formattedValue}
      ></TextField>
    )
  }

  public predictionItemValueSetter = (params: GridValueSetterParams, field: string, precision: number) => {
    const oldValue = params.row[field].value
    const newValue = Number(params.value)

    if (isNaN(oldValue) && isNaN(newValue)) {
      return { ...params.row }
    }
    // Check if the user has edited the value. If so, update the value and choice to reflect the Manual edit.
    if (newValue.toFixed(precision) !== params.row[field].value.toFixed(precision)) {
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

  public predictionItemValueGetter = (params: Pick<GridValueGetterParams, 'value'>, precision: number) => {
    const value = params?.value?.value
    if (isNaN(value)) {
      return 'NaN'
    }
    return value.toFixed(precision)
  }
}
