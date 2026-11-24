import { type AlertColor, GlobalStyles, List, Stack, Typography } from '@mui/material'
import { styled, type Theme, ThemeProvider, useTheme } from '@mui/material/styles'
import type {
  GridCellParams,
  GridColDef,
  GridColumnGroupingModel,
  GridColumnVisibilityModel,
  GridEventListener
} from '@mui/x-data-grid-pro'
import {
  ModelChoice,
  type ModelType,
  submitMoreCastForecastRecords,
  WeatherDeterminate,
  type WeatherDeterminateType
} from '@wps/api/moreCast2API'
import AboutDataPopover from '@wps/ui/AboutDataPopover'
import type { DateRange } from '@wps/ui/dateRangePicker/types'
import type { MoreCastParams } from '@wps/ui/theme'
import { selectAuthentication } from 'app/rootReducer'
import { ROLES } from 'features/auth/roles'
import { type ColumnVis, DataGridColumns, getTabColumnGroupModel } from 'features/moreCast2/components/DataGridColumns'
import ForecastDataGrid from 'features/moreCast2/components/ForecastDataGrid'
import ForecastPublishResultDialog, {
  type ForecastPublishResult
} from 'features/moreCast2/components/ForecastPublishResultDialog'
import ForecastSummaryDataGrid from 'features/moreCast2/components/ForecastSummaryDataGrid'
import MoreCast2DateRangePicker from 'features/moreCast2/components/MoreCast2DateRangePicker'
import MoreCast2Snackbar from 'features/moreCast2/components/MoreCast2Snackbar'
import ResetForecastButton from 'features/moreCast2/components/ResetForecastButton'
import SaveForecastButton from 'features/moreCast2/components/SaveForecastButton'
import SelectableButton from 'features/moreCast2/components/SelectableButton'
import { MorecastDraftForecast } from 'features/moreCast2/forecastDraft'
import type { MoreCast2ForecastRow, MoreCast2Row, PredictionItem } from 'features/moreCast2/interfaces'
import type { ModelElevationData } from 'features/moreCast2/modelElevation'
import { filterAllVisibleRowsForSimulation, filterRowsForSimulationFromEdited } from 'features/moreCast2/rowFilters'
import { getRowsToSave, isForecastRowPredicate, isRequiredInputSet } from 'features/moreCast2/saveForecasts'
import { selectAllMoreCast2Rows, selectWeatherIndeterminatesLoading } from 'features/moreCast2/slices/dataSlice'
import { selectSelectedStations } from 'features/moreCast2/slices/selectedStationsSlice'
import { fillStationGrassCuringForward, simulateFireWeatherIndices } from 'features/moreCast2/util'
import { cloneDeep, groupBy, isEqual, isNull, isUndefined } from 'lodash'
import { DateTime } from 'luxon'
import type React from 'react'
import { memo, useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import type { AppDispatch } from '@/app/store'
import MorecastAboutDataContent from '@/features/moreCast2/components/MorecastAboutDataContent'
import { setRequiredInputEmpty } from '@/features/moreCast2/slices/validInputSlice'
import { adjustStationTemperatures } from '../temperatureAdjustment'

export interface ColumnClickHandlerProps {
  colDef: GridColDef | null
  contextMenu: {
    mouseX: number
    mouseY: number
  } | null
  updateColumnWithModel: (modelType: ModelType, colDef: GridColDef) => void
  handleClose: () => void
}

const saveShowHideColumnsModelToLocalStorage = (model: Record<string, ColumnVis[]>) => {
  const modelAsString = JSON.stringify(model)
  window.localStorage.setItem(SHOW_HIDE_COLUMNS_LOCAL_STORAGE_KEY, modelAsString)
}

const getColumnDisplayName = (name: string) => {
  if (name.endsWith('_BIAS')) {
    const index = name.indexOf('_BIAS')
    return `${name.slice(0, index)} bias`
  }
  return name
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

const getVisibleColumnsByWeatherParam = (
  weatherParam: string,
  visible: boolean,
  columnVisibilityModel: GridColumnVisibilityModel,
  showHideColumnsModel: Record<string, ColumnVis[]>
) => {
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

// supply the autofill keyframes once because grid inputs skip their own style injection
const inputGlobalStyles = {
  '@keyframes mui-auto-fill': { from: { animationName: 'mui-auto-fill' } },
  '@keyframes mui-auto-fill-cancel': { from: { animationName: 'mui-auto-fill-cancel' } }
}

const getGridTheme = (theme: Theme): Theme => ({
  ...theme,
  components: {
    ...theme.components,
    MuiInputBase: {
      ...theme.components?.MuiInputBase,
      defaultProps: {
        ...theme.components?.MuiInputBase?.defaultProps,
        // reinserting global styles for each cell during scrolling caused lag
        // the shared GlobalStyles instance provides the keyframes instead
        disableInjectingGlobalStyles: true
      }
    }
  }
})

export const Root = styled('div')({
  display: 'flex',
  flexGrow: 1,
  flexDirection: 'column',
  '& .MuiDataGrid-cell': {
    display: 'flex',
    alignItems: 'center'
  }
})

const FORECAST_ERROR_MESSAGE = 'The forecast was not saved; an unexpected error occurred.'
const FORECAST_SAVED_MESSAGE = 'Forecast was successfully saved and sent to Wildfire One.'
const FORECAST_WARN_MESSAGE = 'Invalid forecast values, check highlighted cells for further information.'

const SHOW_HIDE_COLUMNS_LOCAL_STORAGE_KEY = 'showHideColumnsModel'

const storedDraftForecast = new MorecastDraftForecast(localStorage)

export interface ElevationAdjustmentHandle {
  applyElevationAdjustment: (
    stationCode: number,
    model: string,
    adjustmentCelsius: number,
    overwriteExisting?: boolean
  ) => string
}

interface TabbedDataGridProps {
  ref?: React.Ref<ElevationAdjustmentHandle>
  fromTo: DateRange
  setFromTo: React.Dispatch<React.SetStateAction<DateRange>>
  fetchWeatherIndeterminates: () => void
  modelElevationData: ModelElevationData
  onCompareElevations: (stationCode: number) => void
}

export type handleShowHideChangeType = (weatherParam: keyof MoreCastParams, columnName: string, value: boolean) => void

const TabbedDataGrid = ({
  ref,
  fromTo,
  setFromTo,
  fetchWeatherIndeterminates,
  modelElevationData,
  onCompareElevations
}: TabbedDataGridProps) => {
  // store
  const dispatch: AppDispatch = useDispatch()
  const selectedStations = useSelector(selectSelectedStations)
  const loading = useSelector(selectWeatherIndeterminatesLoading)
  const { roles, isAuthenticated } = useSelector(selectAuthentication)
  // All MoreCast2Rows derived from WeatherIndeterminates in dataSlice.ts. Updates in response to
  // a change of station group or date range.
  const morecast2Rows = useSelector(selectAllMoreCast2Rows)

  // theme
  const outerTheme = useTheme()
  const gridTheme = useMemo(() => getGridTheme(outerTheme), [outerTheme])

  // state
  // keep forecast edits separate from the fetched rows
  const [allRows, setAllRows] = useState<MoreCast2Row[]>(morecast2Rows)
  const [clickedColDef, setClickedColDef] = useState<GridColDef | null>(null)
  const [contextMenu, setContextMenu] = useState<{
    mouseX: number
    mouseY: number
  } | null>(null)
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
  const [publishResult, setPublishResult] = useState<ForecastPublishResult | null>(null)

  // derived data
  const visibleRows = useMemo(() => {
    const stationCodes = new Set(selectedStations.map(station => station.station_code))
    return allRows.filter(row => stationCodes.has(row.stationCode))
  }, [allRows, selectedStations])

  const hasForecastRow = visibleRows.some(isForecastRowPredicate)
  const lastSavedDraftDateTime = storedDraftForecast.getLastSavedDraftDateTime()

  // forecast callbacks
  const updateColumnHelper = useCallback(
    (editedRows: MoreCast2Row[]) => {
      // Create a copy of editedRows which will be stored as a draft
      let draftRows = cloneDeep(editedRows)
      const rowsForSimulation = filterAllVisibleRowsForSimulation(editedRows) ?? []

      if (rowsForSimulation.length > 0) {
        const filteredRowsWithIndices = simulateFireWeatherIndices(rowsForSimulation)
        draftRows = draftRows.map(newRow => filteredRowsWithIndices.find(row => row.id === newRow.id) || newRow)
      }
      storedDraftForecast.updateStoredDraftForecasts(draftRows, DateTime.utc())
      let newRows = cloneDeep(allRows)
      newRows = newRows.map(newRow => draftRows.find(row => row.id === newRow.id) || newRow)
      setAllRows(newRows)
    },
    [allRows]
  )

  // elevation adjustment
  const applyElevationAdjustment: ElevationAdjustmentHandle['applyElevationAdjustment'] = useCallback(
    (stationCode, model, adjustmentCelsius, overwriteExisting = false) => {
      const result = adjustStationTemperatures(visibleRows, stationCode, model, adjustmentCelsius, overwriteExisting)
      if (result.rows.length) {
        // include observations and subsequent days so indices keep their starting values
        const changedRows = new Map(result.rows.map(row => [row.id, row]))
        const stationRows = visibleRows.filter(row => row.stationCode === stationCode)
        updateColumnHelper(cloneDeep(stationRows.map(row => changedRows.get(row.id) ?? row)))
      }

      return result.message
    },
    [visibleRows, updateColumnHelper]
  )

  useImperativeHandle(ref, () => ({ applyElevationAdjustment }), [applyElevationAdjustment])

  // forecast editing
  // persistence carries the latest observation through the remaining forecast days
  const updateColumnFromLastActual = useCallback(
    (forecastField: keyof MoreCast2Row, actualField: keyof MoreCast2Row) => {
      const newVisibleRows = cloneDeep(visibleRows)
      // Group our visible rows by station code and work on each group sepearately
      const groupedByStationCode = groupBy(newVisibleRows, 'stationCode')
      for (const values of Object.values(groupedByStationCode)) {
        // Get rows with actuals that have non-NaN values
        const rowsWithActuals: MoreCast2Row[] = values.filter(value => !Number.isNaN(value[actualField] as number))
        // Filter for the row with the most recent forDate as this contains our most recent actual
        let mostRecentRow: MoreCast2Row | undefined
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
        const rowsWithoutActuals: MoreCast2Row[] = values.filter(value => Number.isNaN(value[actualField] as number))
        rowsWithoutActuals.forEach(row => {
          const predictionItem = row[forecastField] as PredictionItem
          predictionItem.choice = ModelChoice.PERSISTENCE
          predictionItem.value = mostRecentValue as number
        })
      }
      updateColumnHelper(newVisibleRows)
    },
    [visibleRows, updateColumnHelper]
  )

  const updateColumnFromModel = useCallback(
    (modelType: ModelType, forecastField: keyof MoreCast2Row, actualField: keyof MoreCast2Row, prefix: string) => {
      const newVisibleRows = cloneDeep(visibleRows)
      // Iterate through all the currently visible rows. If a row has an actual value for the weather parameter of
      // interest we can skip it as we are only concerned with creating new forecasts.
      for (const row of newVisibleRows) {
        // If an actual has a value of NaN, then the forecast field needs to be updated.
        if (Number.isNaN(row[actualField] as number)) {
          const predictionItem = row[forecastField] as PredictionItem
          const sourceKey = `${prefix}${modelType}` as keyof MoreCast2Row
          predictionItem.choice = modelType
          predictionItem.value = (row[sourceKey] as number) ?? NaN
        }
      }
      updateColumnHelper(newVisibleRows)
    },
    [visibleRows, updateColumnHelper]
  )

  // Updates forecast field for a given weather parameter (temp, rh, precip, etc...) based on the
  // model/source selected in the column header menu
  const updateColumnWithModel = useCallback(
    (modelType: ModelType, colDef: GridColDef) => {
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
    },
    [updateColumnFromLastActual, updateColumnFromModel]
  )

  // Handler passed to our datagrids that runs after a row is updated.
  const processRowUpdate = useCallback(
    (newRow: MoreCast2Row) => {
      let filledRows = fillStationGrassCuringForward(newRow, allRows)
      const filteredRows = filterRowsForSimulationFromEdited(newRow, filledRows)
      const filteredRowsWithIndices = simulateFireWeatherIndices(filteredRows)
      // Merge rows that have been updated (ie. filledRows) with rows that have had indices added and save as a draft
      filledRows = filledRows.map(
        filledRow => filteredRowsWithIndices.find(row => row.id === filledRow.id) || filledRow
      )
      storedDraftForecast.updateStoredDraftForecasts(filledRows, DateTime.utc())
      let newRows = cloneDeep(allRows)
      // Merge the copy of existing rows with rows that were updated with simulated indices
      newRows = newRows.map(newRow => filledRows.find(row => row.id === newRow.id) || newRow)
      setAllRows(newRows)
      return newRow
    },
    [allRows]
  )

  // column preferences
  const handleClose = useCallback(() => {
    setContextMenu(null)
  }, [])

  const columnClickHandlerProps = useMemo(
    () => ({
      colDef: clickedColDef,
      contextMenu,
      updateColumnWithModel,
      handleClose
    }),
    [clickedColDef, contextMenu, updateColumnWithModel, handleClose]
  )

  const [columnVisibilityModel, setColumnVisibilityModel] = useState<GridColumnVisibilityModel>(() =>
    DataGridColumns.initGridColumnVisibilityModel(columnClickHandlerProps)
  )

  // Gets the previously stored set of weather model columns for each weather paramter (aka tab).
  const getShowHideColumnsModelFromLocalStorage = () => {
    const modelAsString = window.localStorage.getItem(SHOW_HIDE_COLUMNS_LOCAL_STORAGE_KEY)
    return isNull(modelAsString) ? null : JSON.parse(modelAsString)
  }

  // Initialize current columns with saved visibility and defaults for new columns
  const initShowHideColumnsModel = (): Record<string, ColumnVis[]> => {
    // First check localStorage for an existing model
    const model = getShowHideColumnsModelFromLocalStorage()
    // merge saved choices with current columns so newly added models remain available
    const savedVisibility = new Map<string, boolean>(
      Object.values(model ?? {}).flatMap(columns =>
        (columns as ColumnVis[]).map(column => [column.columnName, column.visible] as const)
      )
    )
    const weatherModelColumns = DataGridColumns.getWeatherModelColumns({
      colDef: clickedColDef,
      contextMenu: contextMenu,
      updateColumnWithModel: updateColumnWithModel,
      handleClose: handleClose
    })
    // provide defaults for all current columns while preserving saved choices
    const showHideColumnsUngroupedState = weatherModelColumns.map((column: GridColDef): ColumnVis => {
      return {
        columnName: column.field,
        displayName: getColumnDisplayName(column.headerName ?? ''),
        visible: savedVisibility.get(column.field) ?? true
      }
    })
    return groupByWeatherParam(showHideColumnsUngroupedState)
  }

  const [showHideColumnsModel, setShowHideColumnsModel] =
    useState<Record<string, ColumnVis[]>>(initShowHideColumnsModel)

  // refs
  const showHideColumnsModelRef = useRef(showHideColumnsModel)
  showHideColumnsModelRef.current = showHideColumnsModel
  const tabVisRef = useRef({ tempVisible, rhVisible, precipVisible, windDirectionVisible, windSpeedVisible })
  tabVisRef.current = { tempVisible, rhVisible, precipVisible, windDirectionVisible, windSpeedVisible }

  // callbacks
  const handleColumnHeaderClick: GridEventListener<'columnHeaderClick'> = useCallback((params, event) => {
    if (
      !isEqual(params.colDef.field, 'stationName') &&
      !isEqual(params.colDef.field, 'forDate') &&
      !params.colDef.field.includes('Calc') &&
      !params.colDef.field.includes('grass')
    ) {
      setClickedColDef(params.colDef)
      setContextMenu(current => (current === null ? { mouseX: event.clientX, mouseY: event.clientY } : null))
    }
  }, [])

  const handleShowHideChange: handleShowHideChangeType = useCallback(
    (weatherParam: keyof MoreCastParams, columnName: string, value: boolean) => {
      setShowHideColumnsModel(prev => {
        const newModel = cloneDeep(prev)
        const changedColumn = newModel[weatherParam].filter(column => column.columnName === columnName)[0]
        changedColumn.visible = value
        saveShowHideColumnsModelToLocalStorage(newModel)
        return newModel
      })
    },
    []
  )

  // Handle a double-click on a cell in the datagrid. We only handle a double-click when the clicking
  // occurs on a cell in a weather model field/column and row where a forecast is being created (ie. the
  // row has no actual value for the weather parameter of interest).
  const handleCellDoubleClick = useCallback(
    (params: GridCellParams) => {
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
      if (Number.isNaN(params.row[actualField])) {
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
    },
    [visibleRows, updateColumnHelper]
  )

  const showSnackbar = (message: string, severity: AlertColor) => {
    setSnackbarMessage(message)
    setSnackbarSeverity(severity)
    setSnackbarOpen(true)
  }

  // publishing
  const handleSaveClick = async () => {
    const rowsToSave: MoreCast2ForecastRow[] = getRowsToSave(visibleRows)

    if (!isRequiredInputSet(rowsToSave)) {
      dispatch(setRequiredInputEmpty({ empty: true }))
      showSnackbar(FORECAST_WARN_MESSAGE, 'warning')
      return
    }

    const result = await submitMoreCastForecastRecords(rowsToSave)
    if (!result.success) {
      showSnackbar(result.errorMessage ?? FORECAST_ERROR_MESSAGE, 'error')
      return
    }

    storedDraftForecast.deleteRowsFromStoredDraft(rowsToSave)
    if (result.wf1Skipped.length > 0) {
      setPublishResult({
        savedCount: rowsToSave.length,
        publishedCount: result.wf1PublishedCount,
        skipped: result.wf1Skipped
      })
    } else {
      showSnackbar(FORECAST_SAVED_MESSAGE, 'success')
    }

    fetchWeatherIndeterminates()
  }

  const handleResetButtonConfirm = () => {
    fetchWeatherIndeterminates()
    storedDraftForecast.clearDraftForecasts()
    setShowResetDialog(false)
  }

  const handleResetClick = () => {
    setShowResetDialog(true)
  }

  // effects
  useEffect(() => {
    const colGroupingModel = getTabColumnGroupModel(showHideColumnsModel, handleShowHideChange)
    setColumnGroupingModel(colGroupingModel)
  }, [showHideColumnsModel, handleShowHideChange])

  useEffect(() => {
    const { tempVisible, rhVisible, precipVisible, windDirectionVisible, windSpeedVisible } = tabVisRef.current
    const visibleTabs: string[] = []
    tempVisible && visibleTabs.push('temp')
    rhVisible && visibleTabs.push('rh')
    precipVisible && visibleTabs.push('precip')
    windDirectionVisible && visibleTabs.push('windDirection')
    windSpeedVisible && visibleTabs.push('windSpeed')
    const visibleColumns: GridColumnVisibilityModel = {}
    for (const param of visibleTabs) {
      if (param in showHideColumnsModel) {
        for (const column of showHideColumnsModel[param]) {
          visibleColumns[column.columnName] = column.visible
        }
      }
    }
    setColumnVisibilityModel(prev => ({ ...prev, ...visibleColumns }))
  }, [showHideColumnsModel])

  useEffect(() => {
    setAllRows(morecast2Rows)
  }, [morecast2Rows])

  useEffect(() => {
    tempVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(prev =>
      getVisibleColumnsByWeatherParam('temp', tempVisible, prev, showHideColumnsModelRef.current)
    )
  }, [tempVisible])

  useEffect(() => {
    rhVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(prev =>
      getVisibleColumnsByWeatherParam('rh', rhVisible, prev, showHideColumnsModelRef.current)
    )
  }, [rhVisible])

  useEffect(() => {
    precipVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(prev =>
      getVisibleColumnsByWeatherParam('precip', precipVisible, prev, showHideColumnsModelRef.current)
    )
  }, [precipVisible])

  useEffect(() => {
    windDirectionVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(prev =>
      getVisibleColumnsByWeatherParam('windDirection', windDirectionVisible, prev, showHideColumnsModelRef.current)
    )
  }, [windDirectionVisible])

  useEffect(() => {
    windSpeedVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(prev =>
      getVisibleColumnsByWeatherParam('windSpeed', windSpeedVisible, prev, showHideColumnsModelRef.current)
    )
  }, [windSpeedVisible])

  useEffect(() => {
    grassCuringVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(prev =>
      getVisibleColumnsByWeatherParam('grassCuring', grassCuringVisible, prev, showHideColumnsModelRef.current)
    )
  }, [grassCuringVisible])

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
  }, [forecastSummaryVisible])

  // render
  return (
    <Root>
      <Stack>
        <Stack
          role="toolbar"
          aria-label="Morecast controls"
          direction="row"
          useFlexGap
          sx={{ flexWrap: 'wrap', alignItems: 'center', gap: 1, p: 1 }}
        >
          <MoreCast2DateRangePicker dateRange={fromTo} setDateRange={setFromTo} />
          <List
            component={Stack}
            direction="row"
            disablePadding
            sx={{ flexWrap: 'wrap', alignItems: 'center', gap: 1, maxWidth: '100%' }}
          >
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
          <Stack
            direction="row"
            useFlexGap
            sx={{ flexWrap: 'wrap', alignItems: 'center', justifyContent: 'flex-end', gap: 1, ml: 'auto' }}
          >
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
                hasForecastRow &&
                forecastSummaryVisible
              }
              label={'Publish to WF1'}
              onClick={handleSaveClick}
            />
          </Stack>
        </Stack>
        <Stack direction="row" sx={{ justifyContent: 'flex-end', px: 1, pb: 0.5, gap: 2, minHeight: '1.5rem' }}>
          {lastSavedDraftDateTime && (
            <Typography data-testid="morecast-draft-status" variant="caption" color="text.secondary">
              Draft saved {lastSavedDraftDateTime}
            </Typography>
          )}
          <AboutDataPopover content={MorecastAboutDataContent} maxWidth={600} testId={'morecast-about-data-popover'} />
        </Stack>
      </Stack>
      {/* keep these styles mounted when switching grids so tab changes do not reinsert them */}
      <ThemeProvider theme={gridTheme}>
        <GlobalStyles styles={inputGlobalStyles} />
        {forecastSummaryVisible ? (
          <ForecastSummaryDataGrid
            loading={loading}
            rows={visibleRows}
            columnClickHandlerProps={columnClickHandlerProps}
            handleColumnHeaderClick={handleColumnHeaderClick}
            processRowUpdate={processRowUpdate}
          />
        ) : (
          <ForecastDataGrid
            loading={loading}
            columnClickHandlerProps={columnClickHandlerProps}
            columnVisibilityModel={columnVisibilityModel}
            setColumnVisibilityModel={setColumnVisibilityModel}
            onCellDoubleClickHandler={handleCellDoubleClick}
            handleColumnHeaderClick={handleColumnHeaderClick}
            columnGroupingModel={columnGroupingModel}
            allMoreCast2Rows={visibleRows}
            modelElevationData={modelElevationData}
            onCompareElevations={onCompareElevations}
            processRowUpdate={processRowUpdate}
          />
        )}
      </ThemeProvider>
      <ForecastPublishResultDialog result={publishResult} onClose={() => setPublishResult(null)} />
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

export default memo(TabbedDataGrid)
