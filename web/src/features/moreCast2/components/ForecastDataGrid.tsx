import { styled } from '@mui/material/styles'
import React from 'react'
import {
  DataGrid,
  GridCallbackDetails,
  GridCellParams,
  GridColDef,
  GridColumnGroupingModel,
  GridColumnVisibilityModel,
  GridEventListener,
  MuiEvent
} from '@mui/x-data-grid'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { LinearProgress } from '@mui/material'
import { DataGridColumns } from 'features/moreCast2/components/DataGridColumns'
import ApplyToColumnMenu from 'features/moreCast2/components/ApplyToColumnMenu'
import { ModelChoice, ModelType } from 'api/moreCast2API'
import { fillStationGrassCuringForward } from 'features/moreCast2/util'
import { storeUserEditedRows } from 'features/moreCast2/slices/dataSlice'
import { AppDispatch } from 'app/store'
import { useDispatch } from 'react-redux'

const PREFIX = 'ForecastDataGrid'

const classes = {
  root: `${PREFIX}-root`
}

const Root = styled('div')(() => ({
  [`&.${classes.root}`]: {
    display: 'flex',
    flexGrow: 1,
    flexDirection: 'column',
    height: '1px'
  }
}))

export interface ForecastDataGridProps {
  loading: boolean
  clickedColDef: GridColDef | null
  contextMenu: {
    mouseX: number
    mouseY: number
  } | null
  columnVisibilityModel: GridColumnVisibilityModel
  setColumnVisibilityModel: React.Dispatch<React.SetStateAction<GridColumnVisibilityModel>>
  onCellDoubleClickHandler: (
    params: GridCellParams,
    event: MuiEvent<React.MouseEvent>,
    details: GridCallbackDetails
  ) => void
  updateColumnWithModel: (modelType: ModelType, colDef: GridColDef) => void
  handleColumnHeaderClick: GridEventListener<'columnHeaderClick'>
  handleClose: () => void
  columnGroupingModel: GridColumnGroupingModel
  allMoreCast2Rows: MoreCast2Row[]
}

const ForecastDataGrid = ({
  loading,
  clickedColDef,
  contextMenu,
  columnVisibilityModel,
  setColumnVisibilityModel,
  onCellDoubleClickHandler,
  updateColumnWithModel,
  handleColumnHeaderClick,
  handleClose,
  columnGroupingModel,
  allMoreCast2Rows
}: ForecastDataGridProps) => {
  const dispatch: AppDispatch = useDispatch()

  const processRowUpdate = async (newRow: MoreCast2Row) => {
    const filledRows = fillStationGrassCuringForward(newRow, allMoreCast2Rows)
    dispatch(storeUserEditedRows(filledRows))

    return newRow
  }

  return (
    <Root className={classes.root} data-testid={`morecast2-data-grid`}>
      <DataGrid
        columnVisibilityModel={columnVisibilityModel}
        onColumnVisibilityModelChange={newModel => setColumnVisibilityModel(newModel)}
        columnGroupingModel={columnGroupingModel}
        experimentalFeatures={{ columnGrouping: true }}
        slots={{
          loadingOverlay: LinearProgress
        }}
        onColumnHeaderClick={handleColumnHeaderClick}
        onCellDoubleClick={onCellDoubleClickHandler}
        loading={loading}
        columns={DataGridColumns.getTabColumns()}
        isCellEditable={params => params.row[params.field] !== ModelChoice.ACTUAL}
        rows={allMoreCast2Rows}
        processRowUpdate={processRowUpdate}
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

export default React.memo(ForecastDataGrid)
