import makeStyles from '@mui/styles/makeStyles'
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

export interface ForecastDataGridProps {
  loading: boolean
  clickedColDef: GridColDef | null
  contextMenu: {
    mouseX: number
    mouseY: number
  } | null
  columnVisibilityModel: GridColumnVisibilityModel
  setColumnVisibilityModel: React.Dispatch<React.SetStateAction<GridColumnVisibilityModel>>
  setClickedColDef: React.Dispatch<React.SetStateAction<GridColDef | null>>
  onCellEditStop: (value: boolean) => void
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

const useStyles = makeStyles(() => ({
  root: {
    display: 'flex',
    flexGrow: 1,
    flexDirection: 'column'
  }
}))

const ForecastDataGrid = ({
  loading,
  clickedColDef,
  contextMenu,
  columnVisibilityModel,
  setColumnVisibilityModel,
  onCellEditStop,
  onCellDoubleClickHandler,
  updateColumnWithModel,
  handleColumnHeaderClick,
  handleClose,
  columnGroupingModel,
  allMoreCast2Rows
}: ForecastDataGridProps) => {
  const classes = useStyles()

  return (
    <div className={classes.root} data-testid={`morecast2-data-grid`}>
      <DataGrid
        columnVisibilityModel={columnVisibilityModel}
        onColumnVisibilityModelChange={newModel => setColumnVisibilityModel(newModel)}
        columnGroupingModel={columnGroupingModel}
        experimentalFeatures={{ columnGrouping: true }}
        components={{
          LoadingOverlay: LinearProgress
        }}
        onColumnHeaderClick={handleColumnHeaderClick}
        onCellEditStop={() => onCellEditStop(true)}
        onCellDoubleClick={onCellDoubleClickHandler}
        loading={loading}
        columns={DataGridColumns.getTabColumns()}
        isCellEditable={params => params.row[params.field] !== ModelChoice.ACTUAL}
        rows={allMoreCast2Rows}
      />
      <ApplyToColumnMenu
        colDef={clickedColDef}
        contextMenu={contextMenu}
        handleClose={handleClose}
        updateColumnWithModel={updateColumnWithModel}
      />
    </div>
  )
}

export default React.memo(ForecastDataGrid)
