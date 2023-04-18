import { List, Stack } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { GridColDef, GridColumnVisibilityModel } from '@mui/x-data-grid'
import { ModelType } from 'api/moreCast2API'
import { DataGridColumns, columnGroupingModel } from 'features/moreCast2/components/DataGridColumns'
import ForecastDataGrid from 'features/moreCast2/components/ForecastDataGrid'
import ForecastSummaryDataGrid from 'features/moreCast2/components/ForecastSummaryDataGrid'
import { MORECAST2_FIELDS } from 'features/moreCast2/components/MoreCast2Field'
import SelectableButton from 'features/moreCast2/components/SelectableButton'
import {
  selectAllMoreCast2Rows,
  selectForecastMoreCast2Rows,
  selectWeatherIndeterminatesLoading
} from 'features/moreCast2/slices/dataSlice'
import React, { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'

interface TabbedDataGridProps {
  clickedColDef: GridColDef | null
  onCellEditStop: (value: boolean) => void
  setClickedColDef: React.Dispatch<React.SetStateAction<GridColDef | null>>
  updateColumnWithModel: (modelType: ModelType, colDef: GridColDef) => void
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

const TabbedDataGrid = ({
  clickedColDef,
  onCellEditStop,
  setClickedColDef,
  updateColumnWithModel
}: TabbedDataGridProps) => {
  const classes = useStyles()

  const allMoreCast2Rows = useSelector(selectAllMoreCast2Rows) || []
  const forecastMorecast2Rows = useSelector(selectForecastMoreCast2Rows) || []
  const loading = useSelector(selectWeatherIndeterminatesLoading)

  const [columnVisibilityModel, setColumnVisibilityModel] = React.useState<GridColumnVisibilityModel>(
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
          rows={forecastMorecast2Rows}
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
          allMoreCast2Rows={allMoreCast2Rows}
        />
      )}
    </div>
  )
}

export default React.memo(TabbedDataGrid)
