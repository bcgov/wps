import React from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { DataGrid, GridColDef, GridEventListener } from '@mui/x-data-grid'
import { ModelChoice, ModelType } from 'api/moreCast2API'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { LinearProgress, Menu, MenuItem } from '@mui/material'
import ApplyToColumnMenu from 'features/moreCast2/components/ApplyToColumnMenu'
import { DataGridColumns } from 'features/moreCast2/components/DataGridColumns'

interface ForecastSummaryDataGridProps {
  loading: boolean
  rows: MoreCast2Row[]
  clickedColDef: GridColDef | null
  contextMenu: {
    mouseX: number
    mouseY: number
  } | null
  onCellEditStop: (value: boolean) => void
  setClickedColDef: React.Dispatch<React.SetStateAction<GridColDef | null>>
  updateColumnWithModel: (modelType: ModelType, colDef: GridColDef) => void
  handleColumnHeaderClick: GridEventListener<'columnHeaderClick'>
  handleClose: () => void
}

const useStyles = makeStyles({
  root: {
    display: 'flex',
    flexGrow: 1
  }
})

const ForecastSummaryDataGrid = ({
  loading,
  rows,
  clickedColDef,
  contextMenu,
  onCellEditStop,
  updateColumnWithModel,
  handleColumnHeaderClick,
  handleClose
}: ForecastSummaryDataGridProps) => {
  const classes = useStyles()

  return (
    <div className={classes.root} data-testid={`morecast2-data-grid`}>
      <DataGrid
        components={{
          LoadingOverlay: LinearProgress
        }}
        initialState={{
          sorting: {
            sortModel: [{ field: 'stationName', sort: 'asc' }]
          }
        }}
        onColumnHeaderClick={handleColumnHeaderClick}
        onCellEditStop={() => onCellEditStop(true)}
        loading={loading}
        columns={DataGridColumns.getSummaryColumns()}
        rows={rows}
        isCellEditable={params => params.row[params.field] !== ModelChoice.ACTUAL}
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
            },
            '&.Mui-focusVisible': {
              backgroundColor: 'transparent' // remove the background color when fovused
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

export default ForecastSummaryDataGrid
