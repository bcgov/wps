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
export class GridNumberRenderer {
  renderHeaderWith = (params: GridColumnHeaderParams) => {
    return <Button>{params.colDef.headerName}</Button>
  }
  renderCellWith = (params: GridRenderCellParams) => (
    <TextField disabled={true} size="small" value={params.formattedValue}></TextField>
  )

  renderForecastCellWith = (params: GridRenderCellParams, field: string) => (
    <TextField
      disabled={false}
      size="small"
      label={params.row[field] && params.row[field].choice}
      value={params.formattedValue}
    ></TextField>
  )

  predictionItemValueSetter = (params: GridValueSetterParams, field: string, precision: number) => {
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

  cellValueGetter = (params: GridValueGetterParams, precision: number) => {
    return isNaN(params?.value) ? 'NaN' : params.value.toFixed(precision)
  }

  predictionItemValueGetter = (params: GridValueGetterParams, precision: number) => {
    const value = params?.value?.value
    if (isNaN(value)) {
      return 'NaN'
    }
    return value.toFixed(precision)
  }

  public generateColDefWith = (field: string, headerName: string, precision: number, width: number) => {
    return {
      field,
      disableColumnMenu: true,
      disabledReorder: true,
      headerName,
      sortable: false,
      type: 'number',
      width,
      renderCell: (params: GridRenderCellParams) => {
        return this.renderCellWith(params)
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
        return this.renderHeaderWith(params)
      },
      renderCell: (params: GridRenderCellParams) => {
        return this.renderForecastCellWith(params, field)
      },
      valueFormatter: (params: GridValueFormatterParams) => {
        return this.valueFormatterWith(params, precision)
      },
      valueGetter: (params: GridValueGetterParams) => this.predictionItemValueGetter(params, precision),
      valueSetter: (params: GridValueSetterParams) => this.valueSetterWith(params, field, precision)
    }
  }

  protected valueFormatterWith = (params: GridValueFormatterParams, precision: number) =>
    this.predictionItemValueFormatter(params, precision)
  protected valueGetterWith = (params: GridValueGetterParams, precision: number) =>
    this.cellValueGetter(params, precision)
  protected predictionitemValueGetterWith = (params: GridValueGetterParams, precision: number) =>
    this.predictionItemValueGetter(params, precision)
  protected valueSetterWith = (params: GridValueSetterParams, field: string, precision: number) =>
    this.predictionItemValueSetter(params, field, precision)
}
