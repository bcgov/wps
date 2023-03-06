import React from 'react'
import makeStyles from '@mui/styles/makeStyles'
import {
  DataGrid,
  GridColDef,
  GridValueFormatterParams,
  GridValueGetterParams,
  GridValueSetterParams
} from '@mui/x-data-grid'
import { isNumber } from 'lodash'
import { DateTime } from 'luxon'
import { ModelChoice } from 'api/moreCast2API'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'

interface MoreCast2DataGridProps {
  rows: MoreCast2ForecastRow[]
}

const useStyles = makeStyles({
  root: {
    display: 'flex',
    flexGrow: 1
  }
})

const NOT_AVAILABLE = 'N/A'

const MoreCast2DataGrid = (props: MoreCast2DataGridProps) => {
  const classes = useStyles()
  const { rows } = props

  const gridColumnDefGenerator = (field: string, headerName: string, precision: number) => {
    return {
      field: field,
      disableColumnMenu: true,
      disableReorder: true,
      editable: true,
      headerName: headerName,
      sortable: false,
      type: 'number',
      width: 120,
      valueFormatter: (params: GridValueFormatterParams) => predictionItemValueFormatter(params, precision),
      valueGetter: (params: GridValueGetterParams) => predictionItemValueGetter(params),
      valueSetter: (params: GridValueSetterParams) => predictionItemValueSetter(params, field)
    }
  }

  const predictionItemValueFormatter = (params: GridValueFormatterParams, precision: number) => {
    const value = params?.value
    return isNumber(value) && !isNaN(value) ? value.toFixed(precision) : NOT_AVAILABLE
  }

  const predictionItemValueGetter = (params: GridValueGetterParams) => {
    return params?.value?.value
  }

  const predictionItemValueSetter = (params: GridValueSetterParams, field: string) => {
    const oldValue = params.row[field].value
    const newValue = Number(params.value)

    if (isNaN(oldValue) && isNaN(newValue)) {
      return { ...params.row }
    }

    if (newValue !== params.row[field].value) {
      params.row[field].choice = ModelChoice.MANUAL
      params.row[field].value = newValue
    }

    return { ...params.row }
  }

  const columns: GridColDef[] = [
    { field: 'stationName', flex: 1, headerName: 'Station', maxWidth: 200 },
    {
      field: 'forDate',
      disableColumnMenu: true,
      disableReorder: true,
      flex: 1,
      headerName: 'Date',
      maxWidth: 250,
      sortable: false,
      valueFormatter: (params: GridValueFormatterParams<DateTime>) => {
        return params.value.toLocaleString(DateTime.DATE_MED)
      }
    },
    gridColumnDefGenerator('temp', 'Temp', 1),
    gridColumnDefGenerator('rh', 'RH', 0),
    gridColumnDefGenerator('windDirection', 'Wind Dir', 0),
    gridColumnDefGenerator('windSpeed', 'Wind Speed', 1),
    gridColumnDefGenerator('precip', 'Precip', 1)
  ]

  return (
    <div className={classes.root} data-testid={`morecast2-data-grid`}>
      <DataGrid columns={columns} rows={rows}></DataGrid>
    </div>
  )
}

export default MoreCast2DataGrid
