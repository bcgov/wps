import { AlertColor, Grid, List, Stack, Typography } from '@mui/material'
import { styled } from '@mui/material/styles'
import { useSelector, useDispatch } from 'react-redux'
import { AppDispatch } from '@/app/store'
import {
  GridCellParams,
  GridColDef,
  GridColumnGroupingModel,
  GridColumnVisibilityModel,
  GridEventListener
} from '@mui/x-data-grid-pro'
import {
  ModelChoice,
  ModelType,
  WeatherDeterminate,
  WeatherDeterminateType,
  submitMoreCastForecastRecords
} from 'api/moreCast2API'
import { getTabColumnGroupModel, ColumnVis, DataGridColumns } from 'features/moreCast2/components/DataGridColumns'
import ForecastDataGrid from 'features/moreCast2/components/ForecastDataGrid'
import ForecastSummaryDataGrid from 'features/moreCast2/components/ForecastSummaryDataGrid'
import SelectableButton from 'features/moreCast2/components/SelectableButton'
import { selectAllMoreCast2Rows, selectWeatherIndeterminatesLoading } from 'features/moreCast2/slices/dataSlice'
import React, { useEffect, useState } from 'react'
import { MoreCast2ForecastRow, MoreCast2Row, PredictionItem } from 'features/moreCast2/interfaces'
import { selectSelectedStations } from 'features/moreCast2/slices/selectedStationsSlice'
import { cloneDeep, groupBy, isEqual, isNull, isUndefined } from 'lodash'
import SaveForecastButton from 'features/moreCast2/components/SaveForecastButton'
import { ROLES } from 'features/auth/roles'
import { selectAuthentication } from 'app/rootReducer'
import { DateRange } from 'components/dateRangePicker/types'
import MoreCast2Snackbar from 'features/moreCast2/components/MoreCast2Snackbar'
import { getRowsToSave, isForecastRowPredicate, isRequiredInputSet } from 'features/moreCast2/saveForecasts'
import MoreCast2DateRangePicker from 'features/moreCast2/components/MoreCast2DateRangePicker'
import { filterAllVisibleRowsForSimulation, filterRowsForSimulationFromEdited } from 'features/moreCast2/rowFilters'
import { fillStationGrassCuringForward, simulateFireWeatherIndices } from 'features/moreCast2/util'
import { MoreCastParams, theme } from 'app/theme'
import { MorecastDraftForecast } from 'features/moreCast2/forecastDraft'
import ResetForecastButton from 'features/moreCast2/components/ResetForecastButton'
import { getDateTimeNowPST } from 'utils/date'
import { setRequiredInputEmpty } from '@/features/moreCast2/slices/validInputSlice'
import AboutDataPopover from '@/components/AboutDataPopover'
import MorecastAboutDataContent from '@/features/moreCast2/components/MorecastAboutDataContent'

export interface ColumnClickHandlerProps {
  colDef: GridColDef | null
  contextMenu: {
    mouseX: number
    mouseY: number
  } | null
  updateColumnWithModel: (modelType: ModelType, colDef: GridColDef) => void
  handleClose: () => void
}

export const Root = styled('div')({
  display: 'flex',
  flexGrow: 1,
  flexDirection: 'column'
})

const FORECAST_ERROR_MESSAGE = 'The forecast was not saved; an unexpected error occurred.'
const FORECAST_SAVED_MESSAGE = 'Forecast was successfully saved and sent to Wildfire One.'
const FORECAST_WARN_MESSAGE = 'Invalid forecast values, check highlighted cells for further information.'

const SHOW_HIDE_COLUMNS_LOCAL_STORAGE_KEY = 'showHideColumnsModel'

const storedDraftForecast = new MorecastDraftForecast(localStorage)

interface TabbedDataGridProps {
  fromTo: DateRange
  setFromTo: React.Dispatch<React.SetStateAction<DateRange>>
  fetchWeatherIndeterminates: () => void
}

export type handleShowHideChangeType = (weatherParam: keyof MoreCastParams, columnName: string, value: boolean) => void

const TabbedDataGrid = ({ fromTo, setFromTo, fetchWeatherIndeterminates }: TabbedDataGridProps) => {
  const dispatch: AppDispatch = useDispatch()
  const selectedStations = useSelector(selectSelectedStations)
  const loading = useSelector(selectWeatherIndeterminatesLoading)
  const { roles, isAuthenticated } = useSelector(selectAuthentication)

  // All MoreCast2Rows derived from WeatherIndeterminates in dataSlice.ts. Updates in response to
  // a change of station group or date range.
  const morecast2Rows = useSelector(selectAllMoreCast2Rows)

  // A copy of the sortedMoreCast2Rows as local state
  const [allRows, setAllRows] = useState<MoreCast2Row[]>(morecast2Rows)
  // A subset of allRows with visibility determined by the currently selected stations
  const [visibleRows, setVisibleRows] = useState<MoreCast2Row[]>([])
  const [clickedColDef, setClickedColDef] = useState<GridColDef | null>(null)
  const [contextMenu, setContextMenu] = useState<{
    mouseX: number
    mouseY: number
  } | null>(null)

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

  const handleClose = () => {
    setContextMenu(null)
  }

  const [columnVisibilityModel, setColumnVisibilityModel] = useState<GridColumnVisibilityModel>({})

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
  const [columnGroupingModel, setColumnGroupingModel] = useState<GridColumnGroupingModel>([])

  const [showResetDialog, setShowResetDialog] = useState(false)

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
    const weatherModelColumns = DataGridColumns.getWeatherModelColumns({
      colDef: clickedColDef,
      contextMenu: contextMenu,
      updateColumnWithModel: updateColumnWithModel,
      handleClose: handleClose
    })
    // Provide default with all columns
    const showHideColumnsUngroupedState = weatherModelColumns.map((column: GridColDef): ColumnVis => {
      return {
        columnName: column.field,
        displayName: getColumnDisplayName(column.headerName ?? ''),
        visible: true
      }
    })
    return groupByWeatherParam(showHideColumnsUngroupedState)
  }

  const [showHideColumnsModel, setShowHideColumnsModel] =
    useState<Record<string, ColumnVis[]>>(initShowHideColumnsModel())

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
    const updatedColumnVisibilityModel = { ...columnVisibilityModel }

    if (weatherParam in showHideColumnsModel) {
      const showHideColumns = showHideColumnsModel[weatherParam] || []
      for (const column of showHideColumns) {
        // If tab is visible, restore column's individual visibility state
        // If tab is hidden, hide all columns for this weather parameter
        updatedColumnVisibilityModel[column.columnName] = visible ? column.visible : false
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
    const colGroupingModel = getTabColumnGroupModel(showHideColumnsModel, handleShowHideChange, allRows)
    // Filter the grouping model to only include visible tabs
    const visibleGroupIds: string[] = []
    if (tempVisible) visibleGroupIds.push('Temp')
    if (rhVisible) visibleGroupIds.push('RH')
    if (precipVisible) visibleGroupIds.push('Precip')
    if (windDirectionVisible) visibleGroupIds.push('Wind Dir')
    if (windSpeedVisible) visibleGroupIds.push('Wind Speed')
    if (grassCuringVisible) visibleGroupIds.push('Grass Curing')

    const filteredGroupingModel = colGroupingModel.filter(
      group => group.groupId === 'ID' || visibleGroupIds.includes(group.groupId)
    )
    setColumnGroupingModel(filteredGroupingModel)
  }, [
    showHideColumnsModel,
    allRows,
    tempVisible,
    rhVisible,
    precipVisible,
    windDirectionVisible,
    windSpeedVisible,
    grassCuringVisible
  ]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    // Build a complete column visibility model that handles both visible and hidden tabs
    const newColumnVisibilityModel = { ...columnVisibilityModel }

    // Map of tab visibility states to weather parameter keys
    const tabStates: { [key: string]: boolean } = {
      temp: tempVisible,
      rh: rhVisible,
      precip: precipVisible,
      windDirection: windDirectionVisible,
      windSpeed: windSpeedVisible,
      grassCuring: grassCuringVisible
    }

    // Update column visibility for each weather parameter
    Object.entries(tabStates).forEach(([param, isVisible]) => {
      // Handle weather model columns from showHideColumnsModel
      if (param in showHideColumnsModel) {
        for (const column of showHideColumnsModel[param]) {
          // If tab is visible, use the column's individual visibility setting
          // If tab is hidden, set all its columns to false
          newColumnVisibilityModel[column.columnName] = isVisible ? column.visible : false
        }
      }

      // Handle forecast columns (which are not in showHideColumnsModel)
      const forecastColumnName = `${param}Forecast`
      if (forecastColumnName in newColumnVisibilityModel || isVisible) {
        newColumnVisibilityModel[forecastColumnName] = isVisible
      }
    })

    setColumnVisibilityModel(newColumnVisibilityModel)
  }, [
    showHideColumnsModel,
    tempVisible,
    rhVisible,
    precipVisible,
    windDirectionVisible,
    windSpeedVisible,
    grassCuringVisible
  ]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setAllRows(morecast2Rows)
  }, [morecast2Rows])

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
    // Manage forecast summary visibility based on weather parameter tabs
    const anyWeatherTabVisible =
      tempVisible || rhVisible || precipVisible || windDirectionVisible || windSpeedVisible || grassCuringVisible

    if (anyWeatherTabVisible) {
      // Turn off forecast summary when any weather parameter tab is selected
      setForecastSummaryVisible(false)
    } else {
      // Turn on forecast summary when no weather parameter tabs are selected
      setForecastSummaryVisible(true)
    }
  }, [tempVisible, rhVisible, precipVisible, windDirectionVisible, windSpeedVisible, grassCuringVisible]) // eslint-disable-line react-hooks/exhaustive-deps

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

  const updateColumnHelper = (editedRows: MoreCast2Row[]) => {
    // Create a copy of editedRows which will be stored as a draft
    let draftRows = cloneDeep(editedRows)
    const rowsForSimulation = filterAllVisibleRowsForSimulation(editedRows) ?? []

    if (rowsForSimulation.length > 0) {
      const filteredRowsWithIndices = simulateFireWeatherIndices(rowsForSimulation)
      draftRows = draftRows.map(newRow => filteredRowsWithIndices.find(row => row.id === newRow.id) || newRow)
    }
    storedDraftForecast.updateStoredDraftForecasts(draftRows, getDateTimeNowPST())
    let newRows = cloneDeep(allRows)
    newRows = newRows.map(newRow => draftRows.find(row => row.id === newRow.id) || newRow)
    setAllRows(newRows)
  }

  // Persistence forecasting. Get the most recent actual and persist it through the rest of the
  // days in this forecast period.
  const updateColumnFromLastActual = (forecastField: keyof MoreCast2Row, actualField: keyof MoreCast2Row) => {
    const newVisibleRows = cloneDeep(visibleRows)
    // Group our visible rows by station code and work on each group sepearately
    const groupedByStationCode = groupBy(newVisibleRows, 'stationCode')
    for (const values of Object.values(groupedByStationCode)) {
      // Get rows with actuals that have non-NaN values
      const rowsWithActuals: MoreCast2Row[] = values.filter(value => !isNaN(value[actualField] as number))
      // Filter for the row with the most recent forDate as this contains our most recent actual
      let mostRecentRow: MoreCast2Row | undefined = undefined
      if (rowsWithActuals.length > 0) {
        mostRecentRow = rowsWithActuals.reduce((a, b) => {
          return a.forDate > b.forDate ? a : b
        }, rowsWithActuals[0])
      }
      // The most recent value from the weather station for the weather parameter of interest
      // (eg. tempActual) which will be applied as the forecast value
      const mostRecentValue = isUndefined(mostRecentRow) ? NaN : mostRecentRow[actualField]
      // Finally, get an array of rows that don't have an actual for the weather parameter of interest
      // and iterate through them to apply the most recent actual as the new forecast value
      const rowsWithoutActuals: MoreCast2Row[] = values.filter(value => isNaN(value[actualField] as number))
      rowsWithoutActuals.forEach(row => {
        const predictionItem = row[forecastField] as PredictionItem
        predictionItem.choice = ModelChoice.PERSISTENCE
        predictionItem.value = mostRecentValue as number
      })
    }
    updateColumnHelper(newVisibleRows)
  }

  const updateColumnFromModel = (
    modelType: ModelType,
    forecastField: keyof MoreCast2Row,
    actualField: keyof MoreCast2Row,
    prefix: string
  ) => {
    const newVisibleRows = cloneDeep(visibleRows)
    // Iterate through all the currently visible rows. If a row has an actual value for the weather parameter of
    // interest we can skip it as we are only concerned with creating new forecasts.
    for (const row of newVisibleRows) {
      // If an actual has a value of NaN, then the forecast field needs to be updated.
      if (isNaN(row[actualField] as number)) {
        const predictionItem = row[forecastField] as PredictionItem
        const sourceKey = `${prefix}${modelType}` as keyof MoreCast2Row
        predictionItem.choice = modelType
        predictionItem.value = (row[sourceKey] as number) ?? NaN
      }
    }
    updateColumnHelper(newVisibleRows)
  }

  // Handle a double-click on a cell in the datagrid. We only handle a double-click when the clicking
  // occurs on a cell in a weather model field/column and row where a forecast is being created (ie. the
  // row has no actual value for the weather parameter of interest).
  const handleCellDoubleClick = (params: GridCellParams) => {
    const headerName = params.colDef.headerName as WeatherDeterminateType
    if (
      !headerName ||
      headerName === WeatherDeterminate.ACTUAL ||
      headerName === WeatherDeterminate.FORECAST ||
      headerName === WeatherDeterminate.GC
    ) {
      // A forecast, actual or GC column was clicked, or there is no value for headerName, nothing to do
      return
    }
    // Make sure we're in a row where a forecast is being created (ie. no actual for this weather parameter)
    const doubleClickedField = params.field
    const index = doubleClickedField.indexOf(headerName)
    const prefix = doubleClickedField.slice(0, index)
    const actualField = `${prefix}Actual`
    if (isNaN(params.row[actualField])) {
      // There is no actual value, so we are in a forecast row and can proceed with updating the
      // forecast field value with the value of the cell that was double-clicked
      const forecastField = `${prefix}Forecast` as keyof MoreCast2Row
      const newVisibleRows = cloneDeep(visibleRows)
      const editedRowIndex = newVisibleRows.findIndex(row => row.id === params.row.id)
      if (editedRowIndex > -1) {
        const editedRow = newVisibleRows[editedRowIndex]
        const editedPredictionItem = editedRow[forecastField] as PredictionItem
        editedPredictionItem.choice = headerName
        editedPredictionItem.value = Number(params.value)
        updateColumnHelper(newVisibleRows)
      }
    }
  }

  const handleSaveClick = async () => {
    const rowsToSave: MoreCast2ForecastRow[] = getRowsToSave(visibleRows)

    if (isRequiredInputSet(rowsToSave)) {
      const result = await submitMoreCastForecastRecords(rowsToSave)
      if (result.success) {
        setSnackbarMessage(FORECAST_SAVED_MESSAGE)
        setSnackbarSeverity('success')
        setSnackbarOpen(true)
        storedDraftForecast.deleteRowsFromStoredDraft(rowsToSave, getDateTimeNowPST())
      } else {
        setSnackbarMessage(result.errorMessage ?? FORECAST_ERROR_MESSAGE)
        setSnackbarSeverity('error')
        setSnackbarOpen(true)
      }
    } else {
      dispatch(setRequiredInputEmpty({ empty: true }))
      setSnackbarMessage(FORECAST_WARN_MESSAGE)
      setSnackbarSeverity('warning')
      setSnackbarOpen(true)
    }
  }

  const handleResetButtonConfirm = () => {
    fetchWeatherIndeterminates()
    storedDraftForecast.clearDraftForecasts()
    setShowResetDialog(false)
  }

  const handleResetClick = () => {
    setShowResetDialog(true)
  }

  // Checks if the displayed rows includes non-Actual rows
  const hasForecastRow = () => {
    return visibleRows.filter(isForecastRowPredicate).length > 0
  }

  const handleShowHideChange: handleShowHideChangeType = (
    weatherParam: keyof MoreCastParams,
    columnName: string,
    value: boolean
  ) => {
    const newModel = cloneDeep(showHideColumnsModel)
    const changedColumn = newModel[weatherParam].filter(column => column.columnName === columnName)[0]
    changedColumn.visible = value
    saveShowHideColumnsModelToLocalStorage(newModel)
    setShowHideColumnsModel(newModel)
  }

  // Handler passed to our datagrids that runs after a row is updated.
  const processRowUpdate = (newRow: MoreCast2Row) => {
    let filledRows = fillStationGrassCuringForward(newRow, allRows)
    const filteredRows = filterRowsForSimulationFromEdited(newRow, filledRows)
    const filteredRowsWithIndices = simulateFireWeatherIndices(filteredRows)
    // Merge rows that have been updated (ie. filledRows) with rows that have had indices added and save as a draft
    filledRows = filledRows.map(filledRow => filteredRowsWithIndices.find(row => row.id === filledRow.id) || filledRow)
    storedDraftForecast.updateStoredDraftForecasts(filledRows, getDateTimeNowPST())
    let newRows = cloneDeep(allRows)
    // Merge the copy of existing rows with rows that were updated with simulated indices
    newRows = newRows.map(newRow => filledRows.find(row => row.id === newRow.id) || newRow)
    setAllRows(newRows)
    return newRow
  }

  return (
    <Root>
      <Grid container justifyContent="space-between" alignItems={'center'}>
        <Grid item>
          <MoreCast2DateRangePicker dateRange={fromTo} setDateRange={setFromTo} />
        </Grid>
        <Grid item sx={{ marginRight: theme.spacing(2), marginBottom: theme.spacing(6) }}>
          <Stack direction="row" spacing={theme.spacing(2)} alignItems={'center'}>
            {storedDraftForecast.getLastSavedDraftDateTime() && (
              <Typography sx={{ fontSize: 12 }}>
                Draft saved {storedDraftForecast.getLastSavedDraftDateTime()}
              </Typography>
            )}
            <ResetForecastButton
              label={'Reset'}
              enabled={storedDraftForecast.hasDraftForecastStored()}
              showResetDialog={showResetDialog}
              setShowResetDialog={setShowResetDialog}
              handleResetButtonConfirm={handleResetButtonConfirm}
              onClick={handleResetClick}
            />
            <SaveForecastButton
              enabled={
                isAuthenticated &&
                roles.includes(ROLES.MORECAST_2.WRITE_FORECAST) &&
                hasForecastRow() &&
                forecastSummaryVisible
              }
              label={'Publish to WF1'}
              onClick={handleSaveClick}
            />
          </Stack>
        </Grid>
      </Grid>
      <Grid container alignItems="center" justifyContent="space-between" sx={{ mb: 2 }}>
        <Grid item>
          <List component={Stack} direction="row">
            <SelectableButton
              dataTestId="temp-tab-button"
              onClick={() => setTempVisible(!tempVisible)}
              selected={tempVisible}
              weatherParam="temp"
            >
              Temp
            </SelectableButton>
            <SelectableButton
              dataTestId="rh-tab-button"
              onClick={() => setRhVisible(!rhVisible)}
              selected={rhVisible}
              weatherParam="rh"
            >
              RH
            </SelectableButton>
            <SelectableButton
              dataTestId="wind-direction-tab-button"
              onClick={() => setWindDirectionVisible(!windDirectionVisible)}
              selected={windDirectionVisible}
              weatherParam="windDirection"
            >
              Wind Direction
            </SelectableButton>
            <SelectableButton
              dataTestId="wind-speed-tab-button"
              onClick={() => setWindSpeedVisible(!windSpeedVisible)}
              selected={windSpeedVisible}
              weatherParam="windSpeed"
            >
              Wind Speed
            </SelectableButton>
            <SelectableButton
              dataTestId="precip-tab-button"
              onClick={() => setPrecipVisible(!precipVisible)}
              selected={precipVisible}
              weatherParam="precip"
            >
              Precip
            </SelectableButton>
            <SelectableButton
              dataTestId="grass-curing-tab-button"
              onClick={() => setGrassCuringVisible(!grassCuringVisible)}
              selected={grassCuringVisible}
              weatherParam="gc"
            >
              Grass Curing
            </SelectableButton>
            <SelectableButton
              dataTestId="summary-tab-button"
              onClick={() => setForecastSummaryVisible(!forecastSummaryVisible)}
              selected={forecastSummaryVisible}
              weatherParam="summary"
            >
              Forecast Summary
            </SelectableButton>
          </List>
        </Grid>
        <Grid item sx={{ marginLeft: 'auto', paddingRight: theme.spacing(2) }}>
          <AboutDataPopover content={MorecastAboutDataContent} maxWidth={450} testId={'morecast-about-data-popover'} />
        </Grid>
      </Grid>
      {forecastSummaryVisible ? (
        <ForecastSummaryDataGrid
          loading={loading}
          rows={visibleRows}
          columnClickHandlerProps={{
            colDef: clickedColDef,
            contextMenu: contextMenu,
            updateColumnWithModel: updateColumnWithModel,
            handleClose: handleClose
          }}
          handleColumnHeaderClick={handleColumnHeaderClick}
          processRowUpdate={processRowUpdate}
        />
      ) : (
        <ForecastDataGrid
          loading={loading}
          columnClickHandlerProps={{
            colDef: clickedColDef,
            contextMenu: contextMenu,
            updateColumnWithModel: updateColumnWithModel,
            handleClose: handleClose
          }}
          columnVisibilityModel={columnVisibilityModel}
          setColumnVisibilityModel={setColumnVisibilityModel}
          onCellDoubleClickHandler={handleCellDoubleClick}
          handleColumnHeaderClick={handleColumnHeaderClick}
          columnGroupingModel={columnGroupingModel}
          allMoreCast2Rows={visibleRows}
          processRowUpdate={processRowUpdate}
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
