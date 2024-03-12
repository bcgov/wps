import React from 'react'
import { styled } from '@mui/material/styles'
import { DataGrid, GridColDef, GridEventListener } from '@mui/x-data-grid'
import { ModelChoice, ModelType } from 'api/moreCast2API'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { LinearProgress } from '@mui/material'
import { DataGridColumns, getSummaryColumnGroupModel } from 'features/moreCast2/components/DataGridColumns'
import { storeUserEditedRows, getSimulatedIndices } from 'features/moreCast2/slices/dataSlice'
import { AppDispatch } from 'app/store'
import { useDispatch } from 'react-redux'
import { filterRowsForSimulationFromEdited } from 'features/moreCast2/rowFilters'
import { fillStationGrassCuringForward } from 'features/moreCast2/util'
import { MORECAST_WEATHER_PARAMS, MoreCastParams, theme } from 'app/theme'
import { MORECAST2_INDEX_FIELDS } from 'features/moreCast2/components/MoreCast2Column'
import { ColumnClickHandlerProps } from 'features/moreCast2/components/TabbedDataGrid'

const PREFIX = 'ForecastSummaryDataGrid'

const classes = {
  root: `${PREFIX}-root`
}

const Root = styled('div')(() => {
  const styles: Record<string, React.CSSProperties> = {
    [`&.${classes.root}`]: {
      display: 'flex',
      flexGrow: 1,
      flexDirection: 'column',
      height: '1px'
    }
  }

  Object.keys(MORECAST_WEATHER_PARAMS).forEach(key => {
    styles[`& .${key}-forecast-header`] = {
      backgroundColor: `${MORECAST_WEATHER_PARAMS[key as keyof MoreCastParams].active}`
    }
  })

  MORECAST2_INDEX_FIELDS.forEach(indexField => {
    styles[`& .${indexField.getField()}-forecast-header`] = {
      backgroundColor: `rgba(0, 51, 102, 1)`,
      color: theme.palette.common.white
    }
  })

  return styles
})

interface ForecastSummaryDataGridProps {
  loading: boolean
  rows: MoreCast2Row[]
  columnClickHandlerProps: ColumnClickHandlerProps
  clickedColDef: GridColDef | null
  contextMenu: {
    mouseX: number
    mouseY: number
  } | null
  updateColumnWithModel: (modelType: ModelType, colDef: GridColDef) => void
  handleColumnHeaderClick: GridEventListener<'columnHeaderClick'>
  handleClose: () => void
}

const ForecastSummaryDataGrid = ({
  loading,
  rows,
  columnClickHandlerProps,
  handleColumnHeaderClick
}: ForecastSummaryDataGridProps) => {
  const dispatch: AppDispatch = useDispatch()

  const processRowUpdate = async (newRow: MoreCast2Row) => {
    const filledRows = fillStationGrassCuringForward(newRow, rows)
    dispatch(storeUserEditedRows(filledRows))

    const rowsForSimulation = filterRowsForSimulationFromEdited(newRow, filledRows)
    if (rowsForSimulation) {
      dispatch(getSimulatedIndices(rowsForSimulation))
    }

    return newRow
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
        experimentalFeatures={{ columnGrouping: true }}
        columnGroupingModel={getSummaryColumnGroupModel()}
        onColumnHeaderClick={handleColumnHeaderClick}
        loading={loading}
        columns={DataGridColumns.getSummaryColumns(columnClickHandlerProps)}
        rows={rows}
        isCellEditable={params => params.row[params.field] !== ModelChoice.ACTUAL}
        processRowUpdate={processRowUpdate}
      />
      {/* <ApplyToColumnMenu
        colDef={columnClickHandlerProps.colDef}
        contextMenu={columnClickHandlerProps.contextMenu}
        handleClose={columnClickHandlerProps.handleClose}
        updateColumnWithModel={columnClickHandlerProps.updateColumnWithModel}
      /> */}
    </Root>
  )
}

export default ForecastSummaryDataGrid
