import React from 'react'
import makeStyles from '@mui/styles/makeStyles'
import { DataGrid, GridColDef, GridEventListener } from '@mui/x-data-grid'
import { ModelChoice, ModelType } from 'api/moreCast2API'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { LinearProgress, Menu, MenuItem } from '@mui/material'
import ApplyToColumnMenu from 'features/moreCast2/components/ApplyToColumnMenu'
import { isEqual } from 'lodash'
import { MORECAST2_FORECAST_FIELDS, MORECAST2_STATION_DATE_FIELDS } from 'features/moreCast2/components/MoreCast2Field'

interface ForecastSummaryDataGridProps {
  loading: boolean
  editMode: boolean
  rows: MoreCast2Row[]
  clickedColDef: GridColDef | null
  onCellEditStop: (value: boolean) => void
  setClickedColDef: React.Dispatch<React.SetStateAction<GridColDef | null>>
  updateColumnWithModel: (modelType: ModelType, colDef: GridColDef) => void
}

const useStyles = makeStyles({
  root: {
    display: 'flex',
    flexGrow: 1
  }
})

const ForecastSummaryDataGrid = ({
  loading,
  editMode,
  rows,
  clickedColDef,
  onCellEditStop,
  setClickedColDef,
  updateColumnWithModel
}: ForecastSummaryDataGridProps) => {
  const classes = useStyles()

  const [contextMenu, setContextMenu] = React.useState<{
    mouseX: number
    mouseY: number
  } | null>(null)

  const handleColumnHeaderClick: GridEventListener<'columnHeaderClick'> = (params, event) => {
    if (!isEqual(params.colDef.field, 'stationName') && !isEqual(params.colDef.field, 'forDate')) {
      setClickedColDef(params.colDef)
      setContextMenu(contextMenu === null ? { mouseX: event.clientX, mouseY: event.clientY } : null)
    }
  }

  const handleClose = () => {
    setContextMenu(null)
  }

  const columns: GridColDef[] = MORECAST2_STATION_DATE_FIELDS.map(field => field.generateColDef(editMode)).concat(
    MORECAST2_FORECAST_FIELDS.map(forecastField => forecastField.generateForecastColDef(editMode))
  )

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
        columns={columns}
        rows={rows}
        isCellEditable={params => (params.row[params.field].choice === ModelChoice.ACTUAL ? false : true)}
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
