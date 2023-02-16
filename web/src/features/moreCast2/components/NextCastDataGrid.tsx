import React from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { DataGrid, GridColDef } from '@mui/x-data-grid'

interface NextCastDataGridProps {
  rows: ForecastRow[]
}

const useStyles = makeStyles({
  root: {
    display: 'flex',
    flexGrow: 1
  }
})

export interface ForecastRow {
  id: number
  station: string
  for_date: number
  temp: number
  rh: number
  windDirection: number
  windSpeed: number
  precip: number
}

const columns: GridColDef[] = [
  { field: 'station', headerName: 'Station', width: 120 },
  {
    field: 'for_date',
    disableColumnMenu: true,
    disableReorder: true,
    headerName: 'Date',
    sortable: false,
    width: 120
    // valueFormatter: (params: GridValueGetterParams<number>) => {
    //   if (isNull(params.value) || isUndefined(params.value)) {
    //     return DateTime.now().toISO()
    //   }
    //   return DateTime.fromSeconds(params.value / 1000).toISO()
    // }
  },
  {
    field: 'temp',
    disableColumnMenu: true,
    disableReorder: true,
    editable: true,
    headerName: 'Temp',
    sortable: false,
    type: 'number',
    width: 120
  },
  {
    field: 'rh',
    disableColumnMenu: true,
    disableReorder: true,
    editable: true,
    headerName: 'RH',
    sortable: false,
    type: 'number',
    width: 120
  },
  {
    field: 'windDirection',
    disableColumnMenu: true,
    disableReorder: true,
    editable: true,
    headerName: 'Wind Dir',
    sortable: false,
    type: 'number',
    width: 120
  },
  {
    field: 'windSpeed',
    disableColumnMenu: true,
    disableReorder: true,
    editable: true,
    headerName: 'Wind Speed',
    sortable: false,
    type: 'number',
    width: 120
  },
  {
    field: 'precip',
    disableColumnMenu: true,
    disableReorder: true,
    editable: true,
    headerName: 'Precip',
    sortable: false,
    type: 'number',
    width: 120
  }
]

const NextCastDataGrid = (props: NextCastDataGridProps) => {
  const classes = useStyles()
  return (
    <div className={classes.root}>
      <DataGrid columns={columns} rows={props.rows} experimentalFeatures={{ newEditingApi: true }}></DataGrid>
    </div>
  )
}

export default NextCastDataGrid
