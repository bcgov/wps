import { AlertColor, List, Stack } from '@mui/material'
import { styled } from '@mui/material/styles'
import {
  GridCellParams,
  GridColDef,
  GridColumnGroupingModel,
  GridColumnVisibilityModel,
  GridEventListener
} from '@mui/x-data-grid'
import {
  ModelChoice,
  ModelType,
  WeatherDeterminate,
  WeatherDeterminateType,
  submitMoreCastForecastRecords
} from 'api/moreCast2API'
import { getColumnGroupingModel, ColumnVis, DataGridColumns } from 'features/moreCast2/components/DataGridColumns'
import ForecastDataGrid from 'features/moreCast2/components/ForecastDataGrid'
import ForecastSummaryDataGrid from 'features/moreCast2/components/ForecastSummaryDataGrid'
import SelectableButton from 'features/moreCast2/components/SelectableButton'
import {
  getSimulatedIndices,
  selectUserEditedRows,
  selectWeatherIndeterminatesLoading,
  storeUserEditedRows
} from 'features/moreCast2/slices/dataSlice'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { MoreCast2ForecastRow, MoreCast2Row, PredictionItem } from 'features/moreCast2/interfaces'
import { selectSelectedStations } from 'features/moreCast2/slices/selectedStationsSlice'
import { cloneDeep, groupBy, isEqual, isNull, isUndefined } from 'lodash'
import SaveForecastButton from 'features/moreCast2/components/SaveForecastButton'
import { ROLES } from 'features/auth/roles'
import { selectAuthentication, selectWf1Authentication } from 'app/rootReducer'
import { DateRange } from 'components/dateRangePicker/types'
import MoreCast2Snackbar from 'features/moreCast2/components/MoreCast2Snackbar'
import { isForecastRowPredicate, getRowsToSave, isForecastValid } from 'features/moreCast2/saveForecasts'
import MoreCast2DateRangePicker from 'features/moreCast2/components/MoreCast2DateRangePicker'
import { AppDispatch } from 'app/store'
import { deepClone } from '@mui/x-data-grid/utils/utils'
import { filterAllVisibleRowsForSimulation } from 'features/moreCast2/rowFilters'
import { mapForecastChoiceLabels } from 'features/moreCast2/util'

export const Root = styled('div')({
  display: 'flex',
  flexGrow: 1,
  flexDirection: 'column'
})

export const SaveButton = styled(SaveForecastButton)(({ theme }) => ({
  position: 'absolute',
  right: theme.spacing(2)
}))

const FORECAST_ERROR_MESSAGE = 'The forecast was not saved; an unexpected error occurred.'
const FORECAST_SAVED_MESSAGE = 'Forecast was successfully saved and sent to Wildfire One.'
const FORECAST_WARN_MESSAGE = 'Forecast not submitted. A forecast can only contain N/A values for the Wind Direction.'

const SHOW_HIDE_COLUMNS_LOCAL_STORAGE_KEY = 'showHideColumnsModel'

interface TabbedDataGridProps {
  morecast2Rows: MoreCast2Row[]
  fromTo: DateRange
  setFromTo: React.Dispatch<React.SetStateAction<DateRange>>
}

export type handleShowHideChangeType = (weatherParam: string, columnName: string, value: boolean) => void

const TabbedDataGrid = ({ morecast2Rows, fromTo, setFromTo }: TabbedDataGridProps) => {
  const dispatch: AppDispatch = useDispatch()
  const selectedStations = useSelector(selectSelectedStations)
  const loading = useSelector(selectWeatherIndeterminatesLoading)
  const { roles, isAuthenticated } = useSelector(selectAuthentication)
  const { wf1Token } = useSelector(selectWf1Authentication)
  const userEditedRows = useSelector(selectUserEditedRows)

  // A copy of the sortedMoreCast2Rows as local state
  const [allRows, setAllRows] = useState<MoreCast2Row[]>(morecast2Rows)
  // A subset of allRows with visibility determined by the currently selected stations
  const [visibleRows, setVisibleRows] = useState<MoreCast2Row[]>([])

  const [columnVisibilityModel, setColumnVisibilityModel] = useState<GridColumnVisibilityModel>(
    DataGridColumns.initGridColumnVisibilityModel()
  )

  const [tempVisible, setTempVisible] = useState(true)
  const [rhVisible, setRhVisible] = useState(false)
  const [precipVisible, setPrecipVisible] = useState(false)
  const [windDirectionVisible, setWindDirectionVisible] = useState(false)
  const [windSpeedVisible, setWindSpeedVisible] = useState(false)
  const [forecastSummaryVisible, setForecastSummaryVisible] = useState(false)
  const [grassCuringVisible, setGrassCuringVisible] = useState(false)

  const [snackbarMessage, setSnackbarMessage] = useState('')
  const [snackbarOpen, setSnackbarOpen] = useState(false)
  const [snackbarSeverity, setSnackbarSeverity] = useState<AlertColor>('success')

  const [showHideColumnsModel, setShowHideColumnsModel] = useState<Record<string, ColumnVis[]>>({})
  const [columnGroupingModel, setColumnGroupingModel] = useState<GridColumnGroupingModel>([])

  const [contextMenu, setContextMenu] = useState<{
    mouseX: number
    mouseY: number
  } | null>(null)

  const handleColumnHeaderClick: GridEventListener<'columnHeaderClick'> = (params, event) => {
    if (
      !isEqual(params.colDef.field, 'stationName') &&
      !isEqual(params.colDef.field, 'forDate') &&
      !params.colDef.field.includes('Calc') &&
      !params.colDef.field.includes('grass')
    ) {
      setClickedColDef(params.colDef)
      setContextMenu(contextMenu === null ? { mouseX: event.clientX, mouseY: event.clientY } : null)
    }
  }

  const handleClose = () => {
    setContextMenu(null)
  }

  const groupByWeatherParam = (ungroupedState: ColumnVis[]) => {
    const grouper = (item: ColumnVis) => {
      const field = item.columnName
      if (field.startsWith('temp')) {
        return 'temp'
      }
      if (field.startsWith('rh')) {
        return 'rh'
      }
      if (field.startsWith('precip')) {
        return 'precip'
      }
      if (field.startsWith('windDirection')) {
        return 'windDirection'
      }
      if (field.startsWith('windSpeed')) {
        return 'windSpeed'
      }
    }
    const groupedState = groupBy(ungroupedState, grouper)
    return groupedState
  }

  const getColumnDisplayName = (name: string) => {
    if (name.endsWith('_BIAS')) {
      const index = name.indexOf('_BIAS')
      return `${name.slice(0, index)} bias`
    }
    return name
  }

  // Given an array of weather parameters (aka tabs) return a GridColumnVisibilityModel object that
  // contains all weather model columns that are visible for each weather parameter.
  const getVisibleColumns = (weatherParams: string[]) => {
    const visibleColumns: GridColumnVisibilityModel = {}
    for (const param of weatherParams) {
      if (param in showHideColumnsModel) {
        for (const column of showHideColumnsModel[param]) {
          visibleColumns[column.columnName] = column.visible
        }
      }
    }
    return visibleColumns
  }

  const getVisibleColumnsByWeatherParam = (weatherParam: string, visible: boolean) => {
    const updatedColumnVisibilityModel = DataGridColumns.updateGridColumnVisibilityModel(
      [{ columnName: weatherParam, visible: visible }],
      columnVisibilityModel
    )
    if (visible) {
      const showHideColumns = showHideColumnsModel[weatherParam] || []
      for (const column of showHideColumns) {
        updatedColumnVisibilityModel[column.columnName] = column.visible
      }
    }
    return updatedColumnVisibilityModel
  }

  // Save the current set of weather model columns for each weather parameter (aka tab) as selected
  // by the user.
  const saveShowHideColumnsModelToLocalStorage = (model: Record<string, ColumnVis[]>) => {
    const modelAsString = JSON.stringify(model)
    window.localStorage.setItem(SHOW_HIDE_COLUMNS_LOCAL_STORAGE_KEY, modelAsString)
  }

  // Gets the previously stored set of weather model columns for each weather paramter (aka tab).
  const getShowHideColumnsModelFromLocalStorage = () => {
    const modelAsString = window.localStorage.getItem(SHOW_HIDE_COLUMNS_LOCAL_STORAGE_KEY)
    return isNull(modelAsString) ? null : JSON.parse(modelAsString)
  }

  // Get the showHideColumnsModel from local storage if it exists, else provide default values.
  const initShowHideColumnsModel = (): Record<string, ColumnVis[]> => {
    // First check localStorage for an existing model
    const model = getShowHideColumnsModelFromLocalStorage()
    if (model) {
      return model
    }
    const weatherModelColumns = DataGridColumns.getWeatherModelColumns()
    // Provide default with all columns
    const showHideColumnsUngroupedState = weatherModelColumns.map((column: GridColDef): ColumnVis => {
      return {
        columnName: column.field,
        displayName: getColumnDisplayName(column.headerName || ''),
        visible: true
      }
    })
    return groupByWeatherParam(showHideColumnsUngroupedState)
  }

  // Return an array of strings representing which weather parameters (aka tabs) are currently visible.
  const getVisibleTabs = () => {
    const visibleTabs = []
    tempVisible && visibleTabs.push('temp')
    rhVisible && visibleTabs.push('rh')
    precipVisible && visibleTabs.push('precip')
    windDirectionVisible && visibleTabs.push('windDirection')
    windSpeedVisible && visibleTabs.push('windSpeed')
    return visibleTabs
  }

  useEffect(() => {
    const initialShowHideColumnsModel = initShowHideColumnsModel()
    setShowHideColumnsModel(initialShowHideColumnsModel)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const colGroupingModel = getColumnGroupingModel(showHideColumnsModel, handleShowHideChange)
    setColumnGroupingModel(colGroupingModel)
  }, [showHideColumnsModel]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const visibleTabs = getVisibleTabs()
    const visibleColumns = getVisibleColumns(visibleTabs)
    const newColumnVisibilityModel = {
      ...columnVisibilityModel,
      ...visibleColumns
    }
    setColumnVisibilityModel(newColumnVisibilityModel)
  }, [showHideColumnsModel]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const labelledRows = mapForecastChoiceLabels(morecast2Rows, deepClone(userEditedRows))
    setAllRows(labelledRows)
  }, [userEditedRows, morecast2Rows])

  useEffect(() => {
    const newVisibleRows: MoreCast2Row[] = []
    const stationCodes = selectedStations.map(station => station.station_code)
    for (const row of allRows) {
      if (!isUndefined(stationCodes.find(code => code == row.stationCode))) {
        newVisibleRows.push(row)
      }
    }
    setVisibleRows(newVisibleRows)
  }, [allRows, selectedStations])

  /********** Start useEffects for managing visibility of column groups *************/

  useEffect(() => {
    tempVisible && setForecastSummaryVisible(false)
    const updatedColumnVisibilityModel = getVisibleColumnsByWeatherParam('temp', tempVisible)
    setColumnVisibilityModel(updatedColumnVisibilityModel)
  }, [tempVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    rhVisible && setForecastSummaryVisible(false)
    const updatedColumnVisibilityModel = getVisibleColumnsByWeatherParam('rh', rhVisible)
    setColumnVisibilityModel(updatedColumnVisibilityModel)
  }, [rhVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    precipVisible && setForecastSummaryVisible(false)
    const updatedColumnVisibilityModel = getVisibleColumnsByWeatherParam('precip', precipVisible)
    setColumnVisibilityModel(updatedColumnVisibilityModel)
  }, [precipVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    windDirectionVisible && setForecastSummaryVisible(false)
    const updatedColumnVisibilityModel = getVisibleColumnsByWeatherParam('windDirection', windDirectionVisible)
    setColumnVisibilityModel(updatedColumnVisibilityModel)
  }, [windDirectionVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setForecastSummaryVisible(false)
    windSpeedVisible && setForecastSummaryVisible(false)
    const updatedColumnVisibilityModel = getVisibleColumnsByWeatherParam('windSpeed', windSpeedVisible)
    setColumnVisibilityModel(updatedColumnVisibilityModel)
  }, [windSpeedVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    grassCuringVisible && setForecastSummaryVisible(false)
    const updatedColumnVisibilityModel = getVisibleColumnsByWeatherParam('grassCuring', grassCuringVisible)
    setColumnVisibilityModel(updatedColumnVisibilityModel)
  }, [grassCuringVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // if the forecast summary is visible, we need to toggle off the weather parameter buttons
    if (forecastSummaryVisible) {
      setTempVisible(false)
      setRhVisible(false)
      setPrecipVisible(false)
      setWindDirectionVisible(false)
      setWindSpeedVisible(false)
      setGrassCuringVisible(false)
    }
  }, [forecastSummaryVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  /********** End useEffects for managing visibility of column groups *************/

  const [clickedColDef, setClickedColDef] = useState<GridColDef | null>(null)

  // Updates forecast field for a given weather parameter (temp, rh, precip, etc...) based on the
  // model/source selected in the column header menu
  const updateColumnWithModel = (modelType: ModelType, colDef: GridColDef) => {
    // The value of coldDef.field will be precipForecast, rhForecast, tempForecast, etc.
    // We need the prefix to help us grab the correct weather model field to update (eg. tempHRDPS,
    // precipGFS, etc.)
    const forecastField = colDef.field as keyof MoreCast2Row
    const index = forecastField.indexOf('Forecast')
    const prefix = forecastField.slice(0, index)
    const actualField = `${prefix}Actual` as keyof MoreCast2Row
    modelType === ModelChoice.PERSISTENCE
      ? updateColumnFromLastActual(forecastField, actualField)
      : updateColumnFromModel(modelType, forecastField, actualField, prefix)
  }

  // Persistence forecasting. Get the most recent actual and persist it through the rest of the
  // days in this forecast period.
  const updateColumnFromLastActual = (forecastField: keyof MoreCast2Row, actualField: keyof MoreCast2Row) => {
    const newRows = [...visibleRows]
    // Group our visible rows by station code and work on each group sepearately
    const groupedByStationCode = groupBy(newRows, 'stationCode')
    for (const values of Object.values(groupedByStationCode)) {
      // Get rows with actuals that have non-NaN values
      const rowsWithActuals: MoreCast2Row[] = values.filter(value => !isNaN(value[actualField] as number))
      // Filter for the row with the most recent forDate as this contains our most recent actual
      const mostRecentRow = rowsWithActuals.reduce((a, b) => {
        return a.forDate > b.forDate ? a : b
      })
      // The most recent value from the weather station for the weather parameter of interest
      // (eg. tempActual) which will be applied as the forecast value
      const mostRecentValue = mostRecentRow[actualField]
      // Finally, get an array of rows that don't have an actual for the weather parameter of interest
      // and iterate through them to apply the most recent actual as the new forecast value
      const rowsWithoutActuals: MoreCast2Row[] = values.filter(value => isNaN(value[actualField] as number))
      rowsWithoutActuals.forEach(row => {
        const predictionItem = row[forecastField] as PredictionItem
        predictionItem.choice = ModelChoice.PERSISTENCE
        predictionItem.value = mostRecentValue as number
      })
    }
    const rowsForSimulation = filterAllVisibleRowsForSimulation(newRows)
    if (rowsForSimulation) {
      dispatch(getSimulatedIndices(rowsForSimulation))
    }

    dispatch(storeUserEditedRows(newRows))
    setVisibleRows(newRows)
  }

  const updateColumnFromModel = (
    modelType: ModelType,
    forecastField: keyof MoreCast2Row,
    actualField: keyof MoreCast2Row,
    prefix: string
  ) => {
    const newRows = [...visibleRows]
    // Iterate through all the currently visible rows. If a row has an actual value for the weather parameter of
    // interest we can skip it as we are only concerned with creating new forecasts.
    for (const row of newRows) {
      // If an actual has a value of NaN, then the forecast field needs to be updated.
      if (isNaN(row[actualField] as number)) {
        const predictionItem = row[forecastField] as PredictionItem
        const sourceKey = `${prefix}${modelType}` as keyof MoreCast2Row
        predictionItem.choice = modelType
        predictionItem.value = (row[sourceKey] as number) ?? NaN
      }
    }
    const rowsForSimulation = filterAllVisibleRowsForSimulation(newRows)
    if (rowsForSimulation) {
      dispatch(getSimulatedIndices(rowsForSimulation))
    }

    dispatch(storeUserEditedRows(newRows))
    setVisibleRows(newRows)
  }

  // Handle a double-click on a cell in the datagrid. We only handle a double-click when the clicking
  // occurs on a cell in a weather model field/column and row where a forecast is being created (ie. the
  // row has no actual value for the weather parameter of interest)
  const handleCellDoubleClick = (params: GridCellParams) => {
    const headerName = params.colDef.headerName as WeatherDeterminateType
    if (
      !headerName ||
      headerName === WeatherDeterminate.ACTUAL ||
      headerName === WeatherDeterminate.FORECAST ||
      params.field.includes('grass')
    ) {
      // A forecast or actual column was clicked, or there is no value for headerName, nothing to do
      return
    }
    // Make sure we're in a row where a forecast is being created (ie. no actual for this weather parameter)
    const doubleClickedField = params.field as keyof MoreCast2Row
    const index = doubleClickedField.indexOf(headerName)
    const prefix = doubleClickedField.slice(0, index)
    const actualField = `${prefix}Actual`
    const forecastField = `${prefix}Forecast`
    const row = params.row
    if (isNaN(row[actualField])) {
      // There is no actual value, so we are in a forecast row and can proceed with updating the
      // forecast field value with the value of the cell that was double-clicked
      row[forecastField].choice = headerName
      row[forecastField].value = params.value
      // We've updated local state directly, so now we have to re-render by calling setVisibleRows
      setVisibleRows([...visibleRows])
    }
  }

  const handleSaveClick = async () => {
    if (isForecastValid(visibleRows) && !isUndefined(wf1Token)) {
      const rowsToSave: MoreCast2ForecastRow[] = getRowsToSave(visibleRows)
      const result = await submitMoreCastForecastRecords(wf1Token, rowsToSave)
      if (result.success) {
        setSnackbarMessage(FORECAST_SAVED_MESSAGE)
        setSnackbarSeverity('success')
        setSnackbarOpen(true)
      } else {
        setSnackbarMessage(result.errorMessage ?? FORECAST_ERROR_MESSAGE)
        setSnackbarSeverity('error')
        setSnackbarOpen(true)
      }
    } else {
      setSnackbarMessage(FORECAST_WARN_MESSAGE)
      setSnackbarSeverity('warning')
      setSnackbarOpen(true)
    }
  }

  // Checks if the displayed rows includes non-Actual rows
  const hasForecastRow = () => {
    return visibleRows.filter(isForecastRowPredicate).length > 0
  }

  const handleShowHideChange: handleShowHideChangeType = (weatherParam: string, columnName: string, value: boolean) => {
    const newModel = cloneDeep(showHideColumnsModel)
    const changedColumn = newModel[weatherParam].filter(column => column.columnName === columnName)[0]
    changedColumn.visible = value
    saveShowHideColumnsModelToLocalStorage(newModel)
    setShowHideColumnsModel(newModel)
  }

  return (
    <Root>
      <MoreCast2DateRangePicker dateRange={fromTo} setDateRange={setFromTo} />
      <SaveButton
        enabled={
          isAuthenticated &&
          roles.includes(ROLES.MORECAST_2.WRITE_FORECAST) &&
          hasForecastRow() &&
          forecastSummaryVisible
        }
        label={'Save Forecast'}
        onClick={handleSaveClick}
      />
      <List component={Stack} direction="row">
        <SelectableButton
          dataTestId="temp-tab-button"
          onClick={() => setTempVisible(!tempVisible)}
          selected={tempVisible}
        >
          Temp
        </SelectableButton>
        <SelectableButton dataTestId="rh-tab-button" onClick={() => setRhVisible(!rhVisible)} selected={rhVisible}>
          RH
        </SelectableButton>
        <SelectableButton
          dataTestId="wind-direction-tab-button"
          onClick={() => setWindDirectionVisible(!windDirectionVisible)}
          selected={windDirectionVisible}
        >
          Wind Direction
        </SelectableButton>
        <SelectableButton
          dataTestId="wind-speed-tab-button"
          onClick={() => setWindSpeedVisible(!windSpeedVisible)}
          selected={windSpeedVisible}
        >
          Wind Speed
        </SelectableButton>
        <SelectableButton
          dataTestId="precip-tab-button"
          onClick={() => setPrecipVisible(!precipVisible)}
          selected={precipVisible}
        >
          Precip
        </SelectableButton>
        <SelectableButton
          dataTestId="grass-curing-tab-button"
          onClick={() => setGrassCuringVisible(!grassCuringVisible)}
          selected={grassCuringVisible}
        >
          Grass Curing
        </SelectableButton>
        <SelectableButton
          dataTestId="summary-tab-button"
          onClick={() => setForecastSummaryVisible(!forecastSummaryVisible)}
          selected={forecastSummaryVisible}
        >
          Forecast Summary
        </SelectableButton>
      </List>
      {forecastSummaryVisible ? (
        <ForecastSummaryDataGrid
          loading={loading}
          rows={visibleRows}
          clickedColDef={clickedColDef}
          contextMenu={contextMenu}
          updateColumnWithModel={updateColumnWithModel}
          handleColumnHeaderClick={handleColumnHeaderClick}
          handleClose={handleClose}
        />
      ) : (
        <ForecastDataGrid
          loading={loading}
          clickedColDef={clickedColDef}
          contextMenu={contextMenu}
          columnVisibilityModel={columnVisibilityModel}
          setColumnVisibilityModel={setColumnVisibilityModel}
          onCellDoubleClickHandler={handleCellDoubleClick}
          updateColumnWithModel={updateColumnWithModel}
          handleColumnHeaderClick={handleColumnHeaderClick}
          handleClose={handleClose}
          columnGroupingModel={columnGroupingModel}
          allMoreCast2Rows={visibleRows}
        />
      )}
      <MoreCast2Snackbar
        autoHideDuration={6000}
        handleClose={() => setSnackbarOpen(false)}
        open={snackbarOpen}
        message={snackbarMessage}
        severity={snackbarSeverity}
      />
    </Root>
  )
}

export default React.memo(TabbedDataGrid)
