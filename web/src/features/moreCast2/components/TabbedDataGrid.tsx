import { AlertColor, FormControl, List, Stack } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { GridColDef, GridColumnVisibilityModel } from '@mui/x-data-grid'
import { ForecastActionChoice, ForecastActionType, ModelType, submitMoreCastForecastRecords } from 'api/moreCast2API'
import { DataGridColumns, columnGroupingModel } from 'features/moreCast2/components/DataGridColumns'
import ForecastDataGrid from 'features/moreCast2/components/ForecastDataGrid'
import ForecastSummaryDataGrid from 'features/moreCast2/components/ForecastSummaryDataGrid'
import SelectableButton from 'features/moreCast2/components/SelectableButton'
import { selectWeatherIndeterminatesLoading } from 'features/moreCast2/slices/dataSlice'
import React, { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import { MoreCast2ForecastRow, MoreCast2Row } from 'features/moreCast2/interfaces'
import { selectSelectedStations } from 'features/moreCast2/slices/selectedStationsSlice'
import { isUndefined } from 'lodash'
import MoreCast2ActionBar from 'features/moreCast2/components/MoreCast2ActionBar'
import SaveForecastButton from 'features/moreCast2/components/SaveForecastButton'
import { ROLES } from 'features/auth/roles'
import { selectAuthentication } from 'app/rootReducer'
import { DateRange } from 'components/dateRangePicker/types'
import MoreCast2Snackbar from 'features/moreCast2/components/MoreCast2Snackbar'

const FORECAST_ERROR_MESSAGE = 'The forecast was not saved; an unexpected error occurred.'
const FORECAST_SAVED_MESSAGE = 'Forecast was successfully saved.'
const FORECAST_WARN_MESSAGE = 'A forecast cannot contain N/A values.'

interface TabbedDataGridProps {
  morecast2Rows: MoreCast2Row[]
  forecastAction: ForecastActionType
  setForecastAction: React.Dispatch<React.SetStateAction<ForecastActionType>>
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

const TabbedDataGrid = ({
  morecast2Rows,
  forecastAction,
  setForecastAction,
  fromTo,
  setFromTo,
  modelType,
  setModelType
}: TabbedDataGridProps) => {
  const classes = useStyles()

  const selectedStations = useSelector(selectSelectedStations)
  const loading = useSelector(selectWeatherIndeterminatesLoading)
  const { roles, isAuthenticated } = useSelector(selectAuthentication)

  // A copy of the sortedMoreCast2Rows as local state
  const [allRows, setAllRows] = useState<MoreCast2Row[]>(morecast2Rows)
  // A subset of allRows with visibility determined by the currently selected stations
  const [visibleRows, setVisibleRows] = useState<MoreCast2Row[]>([])

  const [columnVisibilityModel, setColumnVisibilityModel] = useState<GridColumnVisibilityModel>(
    DataGridColumns.initGridColumnVisibilityModel(forecastAction == ForecastActionChoice.EDIT)
  )

  const [tempVisible, setTempVisible] = useState(true)
  const [rhVisible, setRhVisible] = useState(false)
  const [precipVisible, setPrecipVisible] = useState(false)
  const [windDirectionVisible, setWindDirectionVisible] = useState(false)
  const [windSpeedVisible, setWindSpeedVisible] = useState(false)
  const [forecastSummaryVisible, setForecastSummaryVisible] = useState(false)
  const [forecastIsDirty, setForecastIsDirty] = useState(false)

  const [snackbarMessage, setSnackbarMessage] = useState('')
  const [snackbarOpen, setSnackbarOpen] = useState(false)
  const [snackbarSeverity, setSnackbarSeverity] = useState<AlertColor>('success')

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

  // Updates forecast field for a given weather parameter based on the model/source
  // selected in the column header menu
  const updateColumnWithModel = (modelType: ModelType, colDef: GridColDef) => {
    const newRows = [...visibleRows]
    // The value of field will be precipForecast, rhForecast, tempForecast, etc.
    // We need the prefix to help us grab the correct weather model field to update (eg. tempHRDPS,
    // precipGFS, etc.)
    const field = colDef.field
    const index = field.indexOf('Forecast')
    const prefix = field.slice(0, index)
    const actualField = `${prefix}Actual` as keyof MoreCast2Row

    for (const row of newRows) {
      // Ugly cast required to index into a row object using a string
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const rowAsAny = row as any
      // If an actual exists, then there is no need to update the forecast field
      if (isNaN(rowAsAny[actualField])) {
        rowAsAny[field].choice = modelType
        rowAsAny[field].value = rowAsAny[`${prefix}${modelType}`]
      }
    }
    setVisibleRows(newRows)
  }

  const handleSaveClick = async () => {
    const rowsToSave: MoreCast2ForecastRow[] = visibleRows.flatMap(row => {
      if (
        isUndefined(row.precipForecast) ||
        isUndefined(row.rhForecast) ||
        isUndefined(row.tempForecast) ||
        isUndefined(row.windDirectionForecast) ||
        isUndefined(row.windSpeedForecast)
      ) {
        return []
      }
      return {
        id: row.id,
        stationCode: row.stationCode,
        stationName: row.stationName,
        forDate: row.forDate,
        precip: row.precipForecast,
        rh: row.rhForecast,
        temp: row.tempForecast,
        windDirection: row.windDirectionForecast,
        windSpeed: row.windSpeedForecast
      }
    })

    if (forecastIsValid()) {
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
    for (const row of visibleRows) {
      if (
        !isUndefined(row.precipForecast) &&
        !isUndefined(row.rhForecast) &&
        !isUndefined(row.tempForecast) &&
        !isUndefined(row.windSpeedForecast)
      ) {
        return true
      }
    }
    return false
  }

  // A valid, submittable forecast can't contain NaN for any values
  const forecastIsValid = () => {
    for (const row of visibleRows) {
      if (
        (row.precipForecast && isNaN(row.precipForecast.value)) ||
        (row.rhForecast && isNaN(row.rhForecast.value)) ||
        (row.tempForecast && isNaN(row.tempForecast.value)) ||
        (row.windSpeedForecast && isNaN(row.windSpeedForecast.value))
      ) {
        return false
      }
    }
    return true
  }

  return (
    <>
      <MoreCast2ActionBar
        fromTo={fromTo}
        setFromTo={setFromTo}
        modelType={modelType}
        setModelType={setModelType}
        forecastAction={forecastAction}
        setForecastAction={setForecastAction}
      >
        <FormControl className={classes.actionButtonContainer}>
          <SaveForecastButton
            enabled={
              roles.includes(ROLES.MORECAST_2.WRITE_FORECAST) &&
              forecastIsDirty &&
              hasForecastRow() &&
              isAuthenticated &&
              forecastAction === ForecastActionChoice.CREATE
            }
            label={forecastAction === ForecastActionChoice.CREATE ? 'Save Forecast' : 'Update Forecast'}
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
          editMode={forecastAction == ForecastActionChoice.EDIT}
          rows={visibleRows}
          clickedColDef={clickedColDef}
          onCellEditStop={setForecastIsDirty}
          setClickedColDef={setClickedColDef}
          updateColumnWithModel={updateColumnWithModel}
        />
      ) : (
        <ForecastDataGrid
          loading={loading}
          editMode={forecastAction == ForecastActionChoice.EDIT}
          clickedColDef={clickedColDef}
          columnVisibilityModel={columnVisibilityModel}
          setColumnVisibilityModel={setColumnVisibilityModel}
          setClickedColDef={setClickedColDef}
          onCellEditStop={setForecastIsDirty}
          updateColumnWithModel={updateColumnWithModel}
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
