import React, { useEffect } from 'react'
import makeStyles from '@mui/styles/makeStyles'
import {
  DataGrid,
  GridColDef,
  GridColumnHeaderParams,
  GridEventListener,
  GridRenderCellParams,
  GridValueFormatterParams,
  GridValueGetterParams,
  GridValueSetterParams
} from '@mui/x-data-grid'
import { DateTime } from 'luxon'
import { ModelChoice, ModelType } from 'api/moreCast2API'
import { MoreCast2ForecastRow, PredictionItem } from 'features/moreCast2/interfaces'
import { Button, LinearProgress, Menu, MenuItem, TextField } from '@mui/material'
import { useDispatch, useSelector } from 'react-redux'
import { selectColumnModelStationPredictions, selectMorecast2TableLoading } from 'app/rootReducer'
import ApplyToColumnMenu from 'features/moreCast2/components/ApplyToColumnMenu'
import { AppDispatch } from 'app/store'
import { isEqual, isNull } from 'lodash'
import { getColumnModelStationPredictions } from 'features/moreCast2/slices/columnModelSlice'
import { DateRange } from 'components/dateRangePicker/types'

interface MoreCast2DataGridProps {
  fromTo: DateRange
  modelType: ModelType
  rows: MoreCast2ForecastRow[]
  setRows: React.Dispatch<React.SetStateAction<MoreCast2ForecastRow[]>>
}

const useStyles = makeStyles({
  root: {
    display: 'flex',
    flexGrow: 1
  }
})

const NOT_AVAILABLE = 'N/A'

const MoreCast2DataGrid = ({ rows, setRows, fromTo }: MoreCast2DataGridProps) => {
  const classes = useStyles()
  const dispatch: AppDispatch = useDispatch()

  const { stationPredictions, colField, modelType } = useSelector(selectColumnModelStationPredictions)
  const [clickedColDef, setClickedColDef] = React.useState<GridColDef | null>(null)
  const updateColumnWithModel = (modelType: ModelType, colDef: GridColDef) => {
    dispatch(
      getColumnModelStationPredictions(
        rows.map(r => r.stationCode),
        modelType,
        colDef,
        DateTime.fromJSDate(fromTo.startDate ? fromTo.startDate : new Date()).toISODate(),
        DateTime.fromJSDate(fromTo.endDate ? fromTo.endDate : new Date()).toISODate()
      )
    )
  }

  const [contextMenu, setContextMenu] = React.useState<{
    mouseX: number
    mouseY: number
  } | null>(null)

  useEffect(() => {
    if (!isNull(colField) && !isNull(modelType)) {
      const newRows = rows.map(r => ({ ...r }))
      const predictionItem: PredictionItem = { value: 42, choice: modelType }
      newRows.forEach(row => {
        // @ts-ignore
        row[colField as keyof MoreCast2ForecastRow] = { ...predictionItem }
      })
      setRows(newRows)
    }
  }, [stationPredictions, colField, modelType]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleColumnHeaderClick: GridEventListener<'columnHeaderClick'> = (params, event) => {
    if (!isEqual(params.colDef.field, 'stationName') && !isEqual(params.colDef.field, 'forDate')) {
      setClickedColDef(params.colDef)
      setContextMenu(contextMenu === null ? { mouseX: event.clientX, mouseY: event.clientY } : null)
    }
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
      renderHeader: (params: GridColumnHeaderParams) => {
        return <Button>{params.colDef.headerName}</Button>
      },
      renderCell: (params: GridRenderCellParams) => (
        <TextField size="small" label={params.row[field].choice} value={params.formattedValue}></TextField>
      ),
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
        onColumnHeaderClick={handleColumnHeaderClick}
        loading={loading}
        columns={columns}
        rows={rows}
      ></DataGrid>
      <Menu
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
          disableRipple
          sx={{
            '&:hover': {
              backgroundColor: 'transparent' // remove the background color on hover
            },
            '&.Mui-selected': {
              backgroundColor: 'transparent' // remove the background color when selected
            }
          }}
        >
          <ApplyToColumnMenu
            colDef={clickedColDef}
            handleClose={handleClose}
            updateColumnWithModel={updateColumnWithModel}
          />
        </MenuItem>
      </Menu>
    </div>
  )
}

export default MoreCast2DataGrid
