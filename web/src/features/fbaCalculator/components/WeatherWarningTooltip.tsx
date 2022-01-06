import React, { useEffect, useState } from 'react'
import { makeStyles, Paper } from '@material-ui/core'
import { FBAStation, WeatherWarningStation } from 'api/fbaCalcAPI'
import { FBATableRow } from '../RowManager'
import { useDispatch, useSelector } from 'react-redux'
import { fetchWeatherWarningStations } from '../slices/weatherWarningSlice'
import { selectHistoricFireStations } from 'app/rootReducer'

interface WeatherWarningTooltipProps {
  rows: FBATableRow[]
  stations: FBAStation[]
}

async function csvJSON() {
  const response = await fetch('http://localhost:3000/hist_fires_stations.csv')
  const text = await response.text()

  const lines = text.split('\n')

  const result = []

  const headers: any = lines[0].split(',')

  for (let i = 1; i < lines.length; i++) {
    const obj: any = {}
    const currentline = lines[i].split(',')

    for (let j = 0; j < headers.length; j++) {
      obj[headers[j]] = currentline[j]
    }

    result.push(obj)
  }

  //return result; //JavaScript object
  return JSON.parse(JSON.stringify(result)) //JSON
}

const getHistoricFireDates = async (fbaStations: FBAStation[]) => {
  const results: any = await csvJSON()
  const stationFireDates: any = []
  for (let i = 0; i <= fbaStations.length; i++) {
    if (fbaStations[i] && fbaStations[i].station_code) {
      const fireDateObject: any = {
        stationCode: fbaStations[i].station_code,
        fireDates: []
      }
      for (let j = 0; j <= results.length; j++) {
        if (results[j] && results[j].NEAREST_STATION) {
          if (
            results[j].NEAREST_STATION === fbaStations[i].station_code.toString() &&
            results[j].IGNITION_DATE
          ) {
            fireDateObject.fireDates.push(results[j].IGNITION_DATE)
          }
        }
      }
      stationFireDates.push(fireDateObject)
    }
  }
  console.log(stationFireDates)
  return stationFireDates
}

export const WeatherWarningTooltip = (props: WeatherWarningTooltipProps) => {
  const dispatch = useDispatch()
  const useStyles = makeStyles(theme => ({
    tooltip: {
      borderLeft: '6px solid #FCBA19',
      padding: '10px',
      marginBottom: theme.spacing(8),
      marginTop: '24px'
    }
  }))
  const { fireBehaviourResultStations, error: error } = useSelector(
    selectHistoricFireStations
  )
  const [calculatedResults, setCalculatedResults] =
    useState<WeatherWarningStation | null>(fireBehaviourResultStations)

  console.log(fireBehaviourResultStations)

  const date = '2022-01-05T00:00:00.000-08:00'
  console.log(fetchWeatherWarningStations(date, props.rows))

  const classes = useStyles()

  return (
    <Paper className={classes.tooltip}>
      <div>
        <h4>Weather Warning</h4>
        <p>There were very similar weather conditions at *station* for this *fire*</p>
      </div>
    </Paper>
  )
}
