import { AlertColor, FormControl, List, Stack } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { GridCellParams, GridColDef, GridColumnVisibilityModel, GridEventListener } from '@mui/x-data-grid'
import { ModelChoice, ModelType, submitMoreCastForecastRecords, WeatherModelChoices } from 'api/moreCast2API'
import { DataGridColumns, columnGroupingModel } from 'features/moreCast2/components/DataGridColumns'
import ForecastDataGrid from 'features/moreCast2/components/ForecastDataGrid'
import ForecastSummaryDataGrid from 'features/moreCast2/components/ForecastSummaryDataGrid'
import SelectableButton from 'features/moreCast2/components/SelectableButton'
import { selectWeatherIndeterminatesLoading } from 'features/moreCast2/slices/dataSlice'
import React, { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import { MoreCast2ForecastRow, MoreCast2Row, PredictionItem } from 'features/moreCast2/interfaces'
import { selectSelectedStations } from 'features/moreCast2/slices/selectedStationsSlice'
import { groupBy, isEqual, isUndefined } from 'lodash'
import MoreCast2ActionBar from 'features/moreCast2/components/MoreCast2ActionBar'
import SaveForecastButton from 'features/moreCast2/components/SaveForecastButton'
import { ROLES } from 'features/auth/roles'
import { selectAuthentication } from 'app/rootReducer'
import { DateRange } from 'components/dateRangePicker/types'
import MoreCast2Snackbar from 'features/moreCast2/components/MoreCast2Snackbar'
import { isForecastRowPredicate, getRowsToSave, isForecastValid } from 'features/moreCast2/saveForecasts'

const FORECAST_ERROR_MESSAGE = 'The forecast was not saved; an unexpected error occurred.'
const FORECAST_SAVED_MESSAGE = 'Forecast was successfully saved.'
const FORECAST_WARN_MESSAGE = 'Forecast not submitted. A forecast can only contain N/A values for the Wind Direction.'

interface TabbedDataGridProps {
  morecast2Rows: MoreCast2Row[]
  fetchWeatherIndeterminates: () => void
  fromTo: DateRange
  setFromTo: React.Dispatch<React.SetStateAction<DateRange>>
  modelType: ModelType
  setModelType: React.Dispatch<React.SetStateAction<ModelType>>
}

const useStyles = makeStyles(theme => ({
  button: {
    marginLeft: theme.spacing(1)
  },
  formControl: {
    minWidth: 280,
    margin: theme.spacing(1)
  },
  actionButtonContainer: {
    marginTop: 15
  },
  root: {
    display: 'flex',
    flexGrow: 1,
    flexDirection: 'column'
  }
}))

const TabbedDataGrid = ({ morecast2Rows, fromTo, setFromTo, modelType, setModelType }: TabbedDataGridProps) => {
  const classes = useStyles()

  const selectedStations = useSelector(selectSelectedStations)
  const loading = useSelector(selectWeatherIndeterminatesLoading)
  const { roles, isAuthenticated } = useSelector(selectAuthentication)

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

  const [snackbarMessage, setSnackbarMessage] = useState('')
  const [snackbarOpen, setSnackbarOpen] = useState(false)
  const [snackbarSeverity, setSnackbarSeverity] = useState<AlertColor>('success')

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

  useEffect(() => {
    setAllRows([...morecast2Rows])
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
    tempVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(
      DataGridColumns.updateGridColumnVisibliityModel(
        [{ columnName: 'temp', visible: tempVisible }],
        columnVisibilityModel
      )
    )
  }, [tempVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    rhVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(
      DataGridColumns.updateGridColumnVisibliityModel([{ columnName: 'rh', visible: rhVisible }], columnVisibilityModel)
    )
  }, [rhVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    precipVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(
      DataGridColumns.updateGridColumnVisibliityModel(
        [{ columnName: 'precip', visible: precipVisible }],
        columnVisibilityModel
      )
    )
  }, [precipVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    windDirectionVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(
      DataGridColumns.updateGridColumnVisibliityModel(
        [{ columnName: 'windDirection', visible: windDirectionVisible }],
        columnVisibilityModel
      )
    )
  }, [windDirectionVisible]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    windSpeedVisible && setForecastSummaryVisible(false)
    setColumnVisibilityModel(
      DataGridColumns.updateGridColumnVisibliityModel(
        [{ columnName: 'windSpeed', visible: windSpeedVisible }],
        columnVisibilityModel
      )
    )
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
        DataGridColumns.updateGridColumnVisibliityModel(
          [
            { columnName: 'temp', visible: false },
            { columnName: 'rh', visible: false },
            { columnName: 'precip', visible: false },
            { columnName: 'windDirection', visible: false },
            { columnName: 'windSpeed', visible: false }
          ],
          columnVisibilityModel
        )
      )
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
        predictionItem.value = (row[sourceKey] as number) || NaN
      }
    }
    setVisibleRows(newRows)
  }

  // Handle a double-click on a cell in the datagrid. We only handle a double-click when the clicking
  // occurs on a cell in a weather model field/column and row where a forecast is being created (ie. the
  // row has no actual value for the weather parameter of interest)
  const handleCellDoubleClick = (params: GridCellParams) => {
    const headerName = params.colDef.headerName as ModelType
    if (!headerName || WeatherModelChoices.indexOf(headerName) < 0) {
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
    if (isForecastValid(visibleRows)) {
      const rowsToSave: MoreCast2ForecastRow[] = getRowsToSave(visibleRows)
      const result = await submitMoreCastForecastRecords(rowsToSave)
      if (result) {
        setSnackbarMessage(FORECAST_SAVED_MESSAGE)
        setSnackbarSeverity('success')
        setSnackbarOpen(true)
      } else {
        setSnackbarMessage(FORECAST_ERROR_MESSAGE)
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

  return (
    <>
      <MoreCast2ActionBar fromTo={fromTo} setFromTo={setFromTo} modelType={modelType} setModelType={setModelType}>
        <FormControl className={classes.actionButtonContainer}>
          <SaveForecastButton
            enabled={
              isAuthenticated &&
              roles.includes(ROLES.MORECAST_2.WRITE_FORECAST) &&
              hasForecastRow() &&
              forecastSummaryVisible
            }
            label={'Save Forecast'}
            onClick={handleSaveClick}
          />
        </FormControl>
      </MoreCast2ActionBar>
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
        handleClose={() => setSnackbarOpen(!snackbarOpen)}
        open={snackbarOpen}
        message={snackbarMessage}
        severity={snackbarSeverity}
      />
    </>
  )
}

export default React.memo(TabbedDataGrid)
