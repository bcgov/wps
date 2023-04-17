import React, { useEffect, useState } from 'react'
import makeStyles from '@mui/styles/makeStyles'
import {
  DataGrid,
  GridColumnVisibilityModel,
  GridColDef,
  GridColumnGroupingModel,
  GridEventListener
} from '@mui/x-data-grid'
import { ModelType } from 'api/moreCast2API'
// import { RowModel } from 'features/moreCast2/interfaces'
import { LinearProgress, List, Menu, MenuItem, Stack } from '@mui/material'
import { useSelector } from 'react-redux'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import ApplyToColumnMenu from 'features/moreCast2/components/ApplyToColumnMenu'
import { isEqual } from 'lodash'
import { MORECAST2_FIELDS } from 'features/moreCast2/components/MoreCast2Field'
import SelectableButton from 'features/moreCast2/components/SelectableButton'
import { DateTime } from 'luxon'
import { selectAllMoreCast2Rows, selectWeatherIndeterminatesLoading } from 'features/moreCast2/slices/dataSlice'
import { isUndefined } from 'lodash'

interface NewMoreCast2DataGridProps {
  clickedColDef: GridColDef | null
  onCellEditStop: (value: boolean) => void
  setClickedColDef: React.Dispatch<React.SetStateAction<GridColDef | null>>
  updateColumnWithModel: (modelType: ModelType, colDef: GridColDef) => void
}

interface ColumnVis {
  columnName: string
  visible: boolean
}

const useStyles = makeStyles(theme => ({
  button: {
    marginLeft: theme.spacing(1)
  },
  formControl: {
    minWidth: 280,
    margin: theme.spacing(1)
  },
  root: {
    display: 'flex',
    flexGrow: 1,
    flexDirection: 'column'
  }
}))

const NewMoreCast2DataGrid = ({
  clickedColDef,
  onCellEditStop,
  setClickedColDef,
  updateColumnWithModel
}: NewMoreCast2DataGridProps) => {
  const classes = useStyles()

  const [tempVisible, setTempVisible] = useState(true)
  const [rhVisible, setRhVisible] = useState(false)
  const [precipVisible, setPrecipVisible] = useState(false)
  const [windDirectionVisible, setWindDirectionVisible] = useState(false)
  const [windSpeedVisible, setWindSpeedVisible] = useState(false)
  const [forecastSummaryVisible, setForecastSummaryVisible] = useState(false)

  const allMoreCast2Rows = useSelector(selectAllMoreCast2Rows) || []

  useEffect(() => {
    tempVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(updateGridColumnVisibliityModel([{ columnName: 'temp', visible: tempVisible }]))
  }, [tempVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    rhVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(updateGridColumnVisibliityModel([{ columnName: 'rh', visible: rhVisible }]))
  }, [rhVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    precipVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(updateGridColumnVisibliityModel([{ columnName: 'precip', visible: precipVisible }]))
  }, [precipVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    windDirectionVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(
      updateGridColumnVisibliityModel([{ columnName: 'windDirection', visible: windDirectionVisible }])
    )
  }, [windDirectionVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    windSpeedVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(updateGridColumnVisibliityModel([{ columnName: 'windSpeed', visible: windSpeedVisible }]))
  }, [windSpeedVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // if the forecast summary is visible, we need to toggle off the weather parameter buttons
    if (forecastSummaryVisible) {
      setTempVisible(false)
      setRhVisible(false)
      setPrecipVisible(false)
      setWindDirectionVisible(false)
      setWindSpeedVisible(false)
      setColumnVisibilityModel(
        updateGridColumnVisibliityModel([
          { columnName: 'temp', visible: false },
          { columnName: 'rh', visible: false },
          { columnName: 'precip', visible: false },
          { columnName: 'windDirection', visible: false },
          { columnName: 'windSpeed', visible: false }
        ])
      )
    }
  }, [forecastSummaryVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  const DEFAULT_COLUMN_WIDTH = 70

  // const columns: GridColDef[] = [
  //   { field: 'stationName', headerName: 'Station' },
  //   { field: 'forDate', headerName: 'Date', width: 250 },

  //   { field: 'tempPrediction', headerName: 'Forecast', width: DEFAULT_COLUMN_WIDTH, editable: true },
  //   { field: 'tempActual', headerName: 'Actual', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'tempHRDPS', headerName: 'HRDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'tempRDPS', headerName: 'RDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'tempGDPS', headerName: 'GDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'tempGFS', headerName: 'GFS', width: DEFAULT_COLUMN_WIDTH },

  //   { field: 'rhPrediction', headerName: 'Forecast', width: DEFAULT_COLUMN_WIDTH, editable: true },
  //   { field: 'rhActual', headerName: 'Actual', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'rhHRDPS', headerName: 'HRDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'rhRDPS', headerName: 'RDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'rhGDPS', headerName: 'GDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'rhGFS', headerName: 'GFS', width: DEFAULT_COLUMN_WIDTH },

  //   { field: 'precipPrediction', headerName: 'Forecast', width: DEFAULT_COLUMN_WIDTH, editable: true },
  //   { field: 'precipActual', headerName: 'Actual', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'precipHRDPS', headerName: 'HRDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'precipRDPS', headerName: 'RDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'precipGDPS', headerName: 'GDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'precipGFS', headerName: 'GFS', width: DEFAULT_COLUMN_WIDTH },

  //   { field: 'windDirectionPrediction', headerName: 'Forecast', width: DEFAULT_COLUMN_WIDTH, editable: true },
  //   { field: 'windDirectionActual', headerName: 'Actual', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'windDirectionHRDPS', headerName: 'HRDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'windDirectionRDPS', headerName: 'RDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'windDirectionGDPS', headerName: 'GDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'windDirectionGFS', headerName: 'GFS', width: DEFAULT_COLUMN_WIDTH },

  //   { field: 'windSpeedPrediction', headerName: 'Forecast', width: DEFAULT_COLUMN_WIDTH, editable: true },
  //   { field: 'windSpeedActual', headerName: 'Actual', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'windSpeedHRDPS', headerName: 'HRDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'windSpeedRDPS', headerName: 'RDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'windSpeedGDPS', headerName: 'GDPS', width: DEFAULT_COLUMN_WIDTH },
  //   { field: 'windSpeedGFS', headerName: 'GFS', width: DEFAULT_COLUMN_WIDTH }
  // ]

  const columnGroupingModel: GridColumnGroupingModel = [
    {
      groupId: 'ID',
      children: [{ field: 'stationName' }, { field: 'forDate' }]
    },
    {
      groupId: 'Temp',
      children: [
        { field: 'tempForecast' },
        { field: 'tempActual' },
        { field: 'tempHRDPS' },
        { field: 'tempRDPS' },
        { field: 'tempGDPS' },
        { field: 'tempGFS' }
      ]
    },
    {
      groupId: 'RH',
      children: [
        { field: 'rhForecast' },
        { field: 'rhActual' },
        { field: 'rhHRDPS' },
        { field: 'rhRDPS' },
        { field: 'rhGDPS' },
        { field: 'rhGFS' }
      ]
    },
    {
      groupId: 'Precip',
      children: [
        { field: 'precipForecast' },
        { field: 'precipActual' },
        { field: 'precipHRDPS' },
        { field: 'precipRDPS' },
        { field: 'precipGDPS' },
        { field: 'precipGFS' }
      ]
    },
    {
      groupId: 'Wind Dir',
      children: [
        { field: 'windDirectionForecast' },
        { field: 'windDirectionActual' },
        { field: 'windDirectionHRDPS' },
        { field: 'windDirectionRDPS' },
        { field: 'windDirectionGDPS' },
        { field: 'windDirectionGFS' }
      ]
    },
    {
      groupId: 'Wind Speed',
      children: [
        { field: 'windSpeedForecast' },
        { field: 'windSpeedActual' },
        { field: 'windSpeedHRDPS' },
        { field: 'windSpeedRDPS' },
        { field: 'windSpeedGDPS' },
        { field: 'windSpeedGFS' }
      ]
    }
  ]

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

  const loading = useSelector(selectWeatherIndeterminatesLoading)

  let columns: GridColDef[] = []
  MORECAST2_FIELDS.forEach(field => {
    columns = [...columns, ...field.generateColDefs()]
  })

  // const getWeatherParameterColumns = (): string[] => {
  //   const headerNames = columns.map(column => column.headerName)
  //   const definedHeaderNames: string[] = []
  //   for (const headerName of headerNames) {
  //     if (!isUndefined(headerName)) {
  //       definedHeaderNames.push(headerName)
  //     }
  //   }
  //   return definedHeaderNames.filter(
  //     headerName => headerName && headerName !== 'stationName' && headerName !== 'forDate'
  //   )
  // }

  const getWeatherParameterColumns = (): string[] => {
    const fields = columns.map(column => column.field)
    return fields.filter(field => field !== 'stationName' && field !== 'forDate')
  }

  // const weatherParameterColumns = [
  //   'tempPrediction',
  //   'tempActual',
  //   'tempHRDPS',
  //   'tempGDPS',
  //   'tempRDPS',
  //   'tempGFS',
  //   'rhPrediction',
  //   'rhActual',
  //   'rhHRDPS',
  //   'rhGDPS',
  //   'rhRDPS',
  //   'rhGFS',
  //   'precipPrediction',
  //   'precipActual',
  //   'precipHRDPS',
  //   'precipGDPS',
  //   'precipRDPS',
  //   'precipGFS',
  //   'windDirectionPrediction',
  //   'windDirectionActual',
  //   'windDirectionHRDPS',
  //   'windDirectionGDPS',
  //   'windDirectionRDPS',
  //   'windDirectionGFS',
  //   'windSpeedPrediction',
  //   'windSpeedActual',
  //   'windSpeedHRDPS',
  //   'windSpeedGDPS',
  //   'windSpeedRDPS',
  //   'windSpeedGFS'
  // ]

  const [columnVisibilityModel, setColumnVisibilityModel] = React.useState<GridColumnVisibilityModel>(
    initGridColumnVisibilityModel()
  )

  function initGridColumnVisibilityModel() {
    const model: GridColumnVisibilityModel = {}
    const weatherParameterColumns = getWeatherParameterColumns()
    weatherParameterColumns.forEach(columnName => {
      if (columnName.startsWith('temp')) {
        model[columnName] = true
      } else {
        model[columnName] = false
      }
    })
    return model
  }

  const updateGridColumnVisibliityModel = (parameters: ColumnVis[]) => {
    const newModel: GridColumnVisibilityModel = {}
    Object.assign(newModel, columnVisibilityModel)

    for (const property in columnVisibilityModel) {
      parameters.forEach(parameter => {
        if (property.startsWith(parameter.columnName)) {
          newModel[property] = parameter.visible
        }
      })
    }
    return newModel
  }

  // const updateGridColumnVisibliityModel = (parameter: string, value: boolean) => {
  //   const newModel: GridColumnVisibilityModel = {}

  //   weatherParameterColumns.forEach(columnName => {
  //     if (columnName.startsWith(parameter)) {
  //       newModel[columnName] = value
  //     } else {
  //       newModel[columnName] = columnVisibilityModel[columnName]
  //     }
  //   })
  //   return newModel
  // }

  return (
    <div className={classes.root} data-testid={`morecast2-data-grid`}>
      <List component={Stack} direction="row">
        <SelectableButton
          className={classes.button}
          onClick={() => setTempVisible(!tempVisible)}
          selected={tempVisible}
        >
          Temp
        </SelectableButton>
        <SelectableButton className={classes.button} onClick={() => setRhVisible(!rhVisible)} selected={rhVisible}>
          RH
        </SelectableButton>
        <SelectableButton
          className={classes.button}
          onClick={() => setPrecipVisible(!precipVisible)}
          selected={precipVisible}
        >
          Precip
        </SelectableButton>
        <SelectableButton
          className={classes.button}
          onClick={() => setWindDirectionVisible(!windDirectionVisible)}
          selected={windDirectionVisible}
        >
          Wind Direction
        </SelectableButton>
        <SelectableButton
          className={classes.button}
          onClick={() => setWindSpeedVisible(!windSpeedVisible)}
          selected={windSpeedVisible}
        >
          Wind Speed
        </SelectableButton>
        <SelectableButton
          className={classes.button}
          onClick={() => setForecastSummaryVisible(!forecastSummaryVisible)}
          selected={forecastSummaryVisible}
        >
          Forecast Summary
        </SelectableButton>
      </List>
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
        loading={loading}
        columns={columns}
        rows={allMoreCast2Rows}
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

export default NewMoreCast2DataGrid
