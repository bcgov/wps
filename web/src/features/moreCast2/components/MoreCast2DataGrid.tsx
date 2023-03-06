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
    {
      field: 'temp',
      disableColumnMenu: true,
      disableReorder: true,
      editable: true,
      headerName: 'Temp',
      sortable: false,
      type: 'number',
      width: 120,
      valueFormatter: params => predictionItemValueFormatter(params, 1),
      valueGetter: params => predictionItemValueGetter(params),
      valueSetter: params => predictionItemValueSetter(params, 'temp')
    },
    {
      field: 'rh',
      disableColumnMenu: true,
      disableReorder: true,
      editable: true,
      headerName: 'RH',
      sortable: false,
      type: 'number',
      width: 120,
      valueFormatter: params => predictionItemValueFormatter(params, 0),
      valueGetter: params => predictionItemValueGetter(params),
      valueSetter: params => predictionItemValueSetter(params, 'rh')
    },
    {
      field: 'windDirection',
      disableColumnMenu: true,
      disableReorder: true,
      editable: true,
      headerName: 'Wind Dir',
      sortable: false,
      type: 'number',
      width: 120,
      valueFormatter: params => predictionItemValueFormatter(params, 0),
      valueGetter: params => predictionItemValueGetter(params),
      valueSetter: params => predictionItemValueSetter(params, 'windDirection')
    },
    {
      field: 'windSpeed',
      disableColumnMenu: true,
      disableReorder: true,
      editable: true,
      headerName: 'Wind Speed',
      sortable: false,
      type: 'number',
      width: 120,
      valueFormatter: params => predictionItemValueFormatter(params, 1),
      valueGetter: params => predictionItemValueGetter(params),
      valueSetter: params => predictionItemValueSetter(params, 'windSpeed')
    },
    {
      field: 'precip',
      disableColumnMenu: true,
      disableReorder: true,
      editable: true,
      headerName: 'Precip',
      sortable: false,
      type: 'number',
      width: 120,
      valueFormatter: params => predictionItemValueFormatter(params, 1),
      valueGetter: params => predictionItemValueGetter(params),
      valueSetter: params => predictionItemValueSetter(params, 'precip')
    }
  ]

  return (
    <div className={classes.root} data-testid={`morecast2-data-grid`}>
      <DataGrid columns={columns} rows={rows}></DataGrid>
    </div>
  )
}

export default MoreCast2DataGrid
