import { List, Stack } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { GridColDef, GridColumnVisibilityModel } from '@mui/x-data-grid'
import { ModelChoice, ModelType } from 'api/moreCast2API'
import { DataGridColumns, columnGroupingModel } from 'features/moreCast2/components/DataGridColumns'
import ForecastDataGrid from 'features/moreCast2/components/ForecastDataGrid'
import ForecastSummaryDataGrid from 'features/moreCast2/components/ForecastSummaryDataGrid'
import { MORECAST2_FIELDS } from 'features/moreCast2/components/MoreCast2Field'
import SelectableButton from 'features/moreCast2/components/SelectableButton'
import {
  selectForecastMoreCast2Rows,
  selectAllMoreCast2Rows,
  selectWeatherIndeterminatesLoading
} from 'features/moreCast2/slices/dataSlice'
import React, { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import { MoreCast2Row } from 'features/moreCast2/interfaces'
import { selectSelectedStations } from 'features/moreCast2/slices/selectedStationsSlice'

interface TabbedDataGridProps {
  onCellEditStop: (value: boolean) => void
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

const TabbedDataGrid = ({ onCellEditStop }: TabbedDataGridProps) => {
  const classes = useStyles()

  const selectedStations = useSelector(selectSelectedStations)
  const loading = useSelector(selectWeatherIndeterminatesLoading)

  // All MoreCast2Rows derived from WeatherIndeterminates in dataSlice.ts. Updates in response to
  // a change of station group or date range.
  const sortedMoreCast2Rows = useSelector(selectAllMoreCast2Rows)
  // A copy of the sortedMoreCast2Rows as local state
  const [allRows, setAllRows] = useState<MoreCast2Row[]>([])
  // A subset of allRows with visibility determined by the currently selected stations
  const [visibleRows, setVisibleRows] = useState<MoreCast2Row[]>([])

  const [columnVisibilityModel, setColumnVisibilityModel] = useState<GridColumnVisibilityModel>(
    DataGridColumns.initGridColumnVisibilityModel()
  )

  let columns: GridColDef[] = []
  MORECAST2_FIELDS.forEach(field => {
    columns = [...columns, ...field.generateColDefs()]
  })

  const [tempVisible, setTempVisible] = useState(true)
  const [rhVisible, setRhVisible] = useState(false)
  const [precipVisible, setPrecipVisible] = useState(false)
  const [windDirectionVisible, setWindDirectionVisible] = useState(false)
  const [windSpeedVisible, setWindSpeedVisible] = useState(false)
  const [forecastSummaryVisible, setForecastSummaryVisible] = useState(false)

  useEffect(() => {
    setAllRows([...sortedMoreCast2Rows])
  }, [sortedMoreCast2Rows])

  useEffect(() => {
    const newVisibleRows: MoreCast2Row[] = []
    const stationCodes = selectedStations.map(station => station.station_code)
    for (const row of allRows) {
      if (stationCodes.indexOf(row.stationCode) > -1) {
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
    // We need the prefix to help us grab the correct weather model field (eg. tempHRDPS, precipGFS, etc.)
    const field = colDef.field
    const index = field.indexOf('Forecast')
    const prefix = field.slice(0, index)
    for (const row of newRows) {
      // Ugly cast required to index into a row object using a string
      const rowAsAny = row as any
      if (rowAsAny[field].choice !== ModelChoice.FORECAST) {
        rowAsAny[field].choice = modelType
        rowAsAny[field].value = rowAsAny[`${prefix}${modelType}`]
      }
    }
    setVisibleRows(newRows)
  }

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
      {forecastSummaryVisible ? (
        <ForecastSummaryDataGrid
          loading={loading}
          rows={visibleRows}
          clickedColDef={clickedColDef}
          onCellEditStop={onCellEditStop}
          setClickedColDef={setClickedColDef}
          updateColumnWithModel={updateColumnWithModel}
        />
      ) : (
        <ForecastDataGrid
          loading={loading}
          clickedColDef={clickedColDef}
          columnVisibilityModel={columnVisibilityModel}
          setColumnVisibilityModel={setColumnVisibilityModel}
          setClickedColDef={setClickedColDef}
          onCellEditStop={onCellEditStop}
          updateColumnWithModel={updateColumnWithModel}
          columnGroupingModel={columnGroupingModel}
          allMoreCast2Rows={visibleRows}
        />
      )}
    </div>
  )
}

export default React.memo(TabbedDataGrid)
