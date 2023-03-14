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
import { Morecast2Field } from 'features/moreCast2/components/MoreCast2Field'

const NOT_AVAILABLE = 'N/A'
export class GridNumberRenderer {
  protected renderHeaderWith = (params: GridColumnHeaderParams) => {
    return <Button>{params.colDef.headerName}</Button>
  }
  protected renderCellWith = (params: GridRenderCellParams, field: Morecast2Field) => (
    <TextField size="small" label={params.row[field].choice} value={params.formattedValue}></TextField>
  )

  predictionItemValueSetter = (params: GridValueSetterParams, field: Morecast2Field, precision: number) => {
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

  predictionItemValueFormatter = (params: GridValueFormatterParams, precision: number) => {
    const value = Number.parseFloat(params?.value)

    return isNaN(value) ? NOT_AVAILABLE : value.toFixed(precision)
  }

  predictionItemValueGetter = (params: GridValueGetterParams, precision: number) => {
    const value = params?.value?.value
    if (isNaN(value)) {
      return 'NaN'
    }
    return value.toFixed(precision)
  }

  public generateColDefWith = (field: Morecast2Field, headerName: string, precision: number) => {
    return {
      field: field,
      disableColumnMenu: true,
      disableReorder: true,
      editable: true,
      headerName: headerName,
      sortable: false,
      type: 'number',
      width: 120,
      renderHeader: (params: GridColumnHeaderParams) => {
        return this.renderHeaderWith(params)
      },
      renderCell: (params: GridRenderCellParams) => {
        return this.renderCellWith(params, field)
      },
      valueFormatter: (params: GridValueFormatterParams) => {
        return this.valueFormatterWith(params, precision)
      },
      valueGetter: (params: GridValueGetterParams) => this.valueGetterWith(params, precision),
      valueSetter: (params: GridValueSetterParams) => this.valueSetterWith(params, field, precision)
    }
  }

  protected valueFormatterWith = (params: GridValueFormatterParams, precision: number) =>
    this.predictionItemValueFormatter(params, precision)
  protected valueGetterWith = (params: GridValueGetterParams, precision: number) =>
    this.predictionItemValueGetter(params, precision)
  protected valueSetterWith = (params: GridValueSetterParams, field: Morecast2Field, precision: number) =>
    this.predictionItemValueSetter(params, field, precision)
}
