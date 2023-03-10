import React from 'react'
import makeStyles from '@mui/styles/makeStyles'
import {
  DataGrid,
  GridColDef,
  GridValueFormatterParams,
  GridValueGetterParams,
  GridValueSetterParams
} from '@mui/x-data-grid'
import { DateTime } from 'luxon'
import { ModelChoice } from 'api/moreCast2API'
import { MoreCast2ForecastRow, PredictionItem } from 'features/moreCast2/interfaces'
import { LinearProgress, Menu, MenuItem } from '@mui/material'
import { useSelector } from 'react-redux'
import { selectMorecast2TableLoading } from 'app/rootReducer'
import ApplyFunctionMenuItem from 'features/moreCast2/components/ApplyFunctionMenuItem'

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
  const [currentRows, setRows] = React.useState(rows)
  const [selectedRow, setSelectedRow] = React.useState<number>()

  if (rows !== currentRows) {
    setRows(rows)
  }

  const [contextMenu, setContextMenu] = React.useState<{
    mouseX: number
    mouseY: number
  } | null>(null)

  const handleContextMenu = (event: React.MouseEvent) => {
    event.preventDefault()
    const column = event.currentTarget.attributes.getNamedItem('data-field')?.value
    if (column) {
      const rowsToAdjust = rows.map(r => {
        ;(r[column as keyof MoreCast2ForecastRow] as PredictionItem).value *= 2
        return r
      })
      console.log(rowsToAdjust)
    }

    setContextMenu(contextMenu === null ? { mouseX: event.clientX - 2, mouseY: event.clientY - 4 } : null)
  }

  const handleClose = () => {
    setContextMenu(null)
  }

  const loading = useSelector(selectMorecast2TableLoading)

  const predictionItemValueFormatter = (params: GridValueFormatterParams, precision: number) => {
    const value = Number.parseFloat(params?.value)

    return isNaN(value) ? NOT_AVAILABLE : value.toFixed(precision)
  }

  const predictionItemValueGetter = (params: GridValueGetterParams, precision: number) => {
    const value = params?.value?.value
    if (isNaN(value)) {
      return 'NaN'
    }
    return value.toFixed(precision)
  }

  const predictionItemValueSetter = (params: GridValueSetterParams, field: string, precision: number) => {
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
      valueGetter: (params: GridValueGetterParams) => predictionItemValueGetter(params, precision),
      valueSetter: (params: GridValueSetterParams) => predictionItemValueSetter(params, field, precision)
    }
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
      <DataGrid
        components={{
          LoadingOverlay: LinearProgress
        }}
        slotProps={{
          // row: {
          //   onContextMenu: handleContextMenu,
          //   style: { cursor: 'context-menu' }
          // },
          cell: {
            onMouseDown: handleContextMenu
          }
        }}
        loading={loading}
        columns={columns}
        rows={currentRows}
      ></DataGrid>
      {/* <Menu
        open={contextMenu !== null}
        onClose={handleClose}
        anchorReference="anchorPosition"
        anchorPosition={contextMenu !== null ? { top: contextMenu.mouseY, left: contextMenu.mouseX } : undefined}
        slotProps={{
          root: {
            onContextMenu: e => {
              e.preventDefault()
              handleClose()
            }
          }
        }}
      >
        <MenuItem
          onClick={() => {
            console.log('Menu item 1')
          }}
        >
          <ApplyFunctionMenuItem />
        </MenuItem>
      </Menu> */}
    </div>
  )
}

export default MoreCast2DataGrid
