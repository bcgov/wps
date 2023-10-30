import React from 'react'
import { styled } from '@mui/material/styles'
import { DataGrid, GridColDef, GridEventListener, GridCellEditStopParams } from '@mui/x-data-grid'
import { ModelChoice, ModelType, fetchCalculatedIndices } from 'api/moreCast2API'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { LinearProgress } from '@mui/material'
import ApplyToColumnMenu from 'features/moreCast2/components/ApplyToColumnMenu'
import { DataGridColumns } from 'features/moreCast2/components/DataGridColumns'
import { isNaN } from 'lodash'
import { rowIDHasher } from 'features/moreCast2/util'
import { validForecastPredicate } from 'features/moreCast2/saveForecasts'
import { updateWeatherIndeterminates, storeUserEditedRows } from 'features/moreCast2/slices/dataSlice'
import { AppDispatch } from 'app/store'
import { useDispatch } from 'react-redux'

const PREFIX = 'ForecastSummaryDataGrid'

const classes = {
  root: `${PREFIX}-root`
}

const Root = styled('div')({
  [`&.${classes.root}`]: {
    display: 'flex',
    flexGrow: 1
  }
})

interface ForecastSummaryDataGridProps {
  loading: boolean
  rows: MoreCast2Row[]
  clickedColDef: GridColDef | null
  contextMenu: {
    mouseX: number
    mouseY: number
  } | null
  updateColumnWithModel: (modelType: ModelType, colDef: GridColDef) => void
  handleColumnHeaderClick: GridEventListener<'columnHeaderClick'>
  handleClose: () => void
}

const getYesterdayRowID = (todayRow: MoreCast2Row): string => {
  const yesterdayDate = todayRow.forDate.minus({ days: 1 })
  const yesterdayID = rowIDHasher(todayRow.stationCode, yesterdayDate)

  return yesterdayID
}

export const validActualPredicate = (row: MoreCast2Row) =>
  !isNaN(row.precipActual) && !isNaN(row.rhActual) && !isNaN(row.tempActual) && !isNaN(row.windSpeedActual)

export const isActualOrValidForecastPredicate = (row: MoreCast2Row) =>
  validForecastPredicate(row) || validActualPredicate(row)

const ForecastSummaryDataGrid = ({
  loading,
  rows,
  clickedColDef,
  contextMenu,
  updateColumnWithModel,
  handleColumnHeaderClick,
  handleClose
}: ForecastSummaryDataGridProps) => {
  const dispatch: AppDispatch = useDispatch()
  const handleCellEditStop = async (params: GridCellEditStopParams) => {
    const editedRow = params.row
    dispatch(storeUserEditedRows([editedRow]))

    const mustBeFilled = [
      editedRow.tempForecast?.value,
      editedRow.rhForecast?.value,
      editedRow.windSpeedForecast?.value,
      editedRow.precipForecast?.value
    ]
    for (const value of mustBeFilled) {
      if (isNaN(value)) {
        return editedRow
      }
    }
    const idBeforeEditedRow = getYesterdayRowID(editedRow)
    const rowsForSimulation = rows.filter(row => row.id >= idBeforeEditedRow).filter(isActualOrValidForecastPredicate)
    const simulatedForecasts = await fetchCalculatedIndices(rowsForSimulation)
    dispatch(updateWeatherIndeterminates(simulatedForecasts))
  }

  return (
    <Root className={classes.root} data-testid={`morecast2-data-grid`}>
      <DataGrid
        slots={{
          loadingOverlay: LinearProgress
        }}
        initialState={{
          sorting: {
            sortModel: [{ field: 'stationName', sort: 'asc' }]
          }
        }}
        onColumnHeaderClick={handleColumnHeaderClick}
        loading={loading}
        columns={DataGridColumns.getSummaryColumns()}
        rows={rows}
        isCellEditable={params => params.row[params.field] !== ModelChoice.ACTUAL}
        onCellEditStop={handleCellEditStop}
      />
      <ApplyToColumnMenu
        colDef={clickedColDef}
        contextMenu={contextMenu}
        handleClose={handleClose}
        updateColumnWithModel={updateColumnWithModel}
      />
    </Root>
  )
}

export default ForecastSummaryDataGrid
