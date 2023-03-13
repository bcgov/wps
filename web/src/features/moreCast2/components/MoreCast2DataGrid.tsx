import React, { useEffect } from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { DataGrid, GridColDef, GridEventListener } from '@mui/x-data-grid'
import { DateTime } from 'luxon'
import { ModelChoice, ModelType } from 'api/moreCast2API'
import { MoreCast2ForecastRow } from 'features/moreCast2/interfaces'
import { LinearProgress, Menu, MenuItem } from '@mui/material'
import { useDispatch, useSelector } from 'react-redux'
import {
  selectColumnModelStationPredictions,
  selectColumnYesterdayDailies,
  selectMorecast2TableLoading
} from 'app/rootReducer'
import ApplyToColumnMenu from 'features/moreCast2/components/ApplyToColumnMenu'
import { AppDispatch } from 'app/store'
import { isEqual, isNull } from 'lodash'
import { getColumnModelStationPredictions } from 'features/moreCast2/slices/columnModelSlice'
import { DateRange } from 'components/dateRangePicker/types'
import {
  MORECAST2_GRID_COLUMNS,
  replaceColumnValuesFromPrediction,
  replaceColumnValuesFromYesterdayDaily
} from 'features/moreCast2/components/morecast2GridColumns'
import { FireCenterStation } from 'api/fbaAPI'
import { getColumnYesterdayDailies } from 'features/moreCast2/slices/columnYesterdaySlice'

interface MoreCast2DataGridProps {
  fromTo: DateRange
  modelType: ModelType
  rows: MoreCast2ForecastRow[]
  fireCentreStations: FireCenterStation[]
  dateInterval: string[]
  setRows: React.Dispatch<React.SetStateAction<MoreCast2ForecastRow[]>>
}

const useStyles = makeStyles({
  root: {
    display: 'flex',
    flexGrow: 1
  }
})

const MoreCast2DataGrid = ({ rows, setRows, fromTo, fireCentreStations, dateInterval }: MoreCast2DataGridProps) => {
  const classes = useStyles()
  const dispatch: AppDispatch = useDispatch()

  const { colPrediction } = useSelector(selectColumnModelStationPredictions)
  const { colYesterdayDailies } = useSelector(selectColumnYesterdayDailies)

  const [clickedColDef, setClickedColDef] = React.useState<GridColDef | null>(null)
  const updateColumnWithModel = (modelType: ModelType, colDef: GridColDef) => {
    if (modelType == ModelChoice.YESTERDAY) {
      dispatch(
        getColumnYesterdayDailies(
          fireCentreStations.map(s => s.code),
          fireCentreStations,
          dateInterval,
          modelType,
          colDef.field as keyof MoreCast2ForecastRow,
          DateTime.fromJSDate(fromTo.startDate ? fromTo.startDate : new Date()).toISODate()
        )
      )
    } else {
      dispatch(
        getColumnModelStationPredictions(
          fireCentreStations.map(s => s.code),
          modelType,
          colDef.field as keyof MoreCast2ForecastRow,
          DateTime.fromJSDate(fromTo.startDate ? fromTo.startDate : new Date()).toISODate(),
          DateTime.fromJSDate(fromTo.endDate ? fromTo.endDate : new Date()).toISODate()
        )
      )
    }
  }

  const [contextMenu, setContextMenu] = React.useState<{
    mouseX: number
    mouseY: number
  } | null>(null)

  useEffect(() => {
    if (!isNull(colPrediction)) {
      const newRows = replaceColumnValuesFromPrediction(rows, fireCentreStations, dateInterval, colPrediction)
      setRows(newRows)
    }
  }, [colPrediction]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isNull(colYesterdayDailies)) {
      const newRows = replaceColumnValuesFromYesterdayDaily(rows, fireCentreStations, dateInterval, colYesterdayDailies)
      setRows(newRows)
    }
  }, [colYesterdayDailies]) // eslint-disable-line react-hooks/exhaustive-deps

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

  const columns: GridColDef[] = MORECAST2_GRID_COLUMNS.map(field => field.generateColDef())

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
