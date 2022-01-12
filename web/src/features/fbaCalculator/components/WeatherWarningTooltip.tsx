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
  return stationFireDates
}

export const WeatherWarningTooltip = (props: WeatherWarningTooltipProps) => {
  const dispatch = useDispatch()
  const useStyles = makeStyles(theme => ({
    tooltip: {
      borderLeft: '6px solid red',
      padding: '5px',
      marginTop: '10px',
      marginBottom: '5px'
    },
    hiddenTooltip: {
      display: 'none'
    }
  }))
  const classes = useStyles()
  const { fireBehaviourResultStations, error: error } = useSelector(
    selectHistoricFireStations
  )
  const [showTooltip, setShowTooltip] = useState<boolean>(false)

  const thisdate = '2021-07-06T00:00:00.000-08:00'
  useEffect(() => {
    dispatch(fetchWeatherWarningStations(thisdate, props.rows))
  }, [props.rows])

  console.log(fireBehaviourResultStations)

  const compareValues = (
    currentStations: FBAStation[],
    historicStation: WeatherWarningStation | null
  ) => {
    if (historicStation !== null) {
      const historicDaily = historicStation.dailies[0]
      console.log(historicDaily)
      currentStations.forEach(station => {
        if (historicDaily.code === station.station_code) {
          console.log(historicDaily)
          const buiDifference = historicDaily.bui * 0.1
          const buiMaxDifference = historicDaily.bui + buiDifference
          const buiMinDifference = historicDaily.bui - buiDifference
          const dmcDifference = historicDaily.dmc * 0.1
          const dmcMaxDifference = historicDaily.dmc + dmcDifference
          const dmcMinDifference = historicDaily.dmc - dmcDifference
          if (
            station.build_up_index < buiMaxDifference &&
            station.build_up_index > buiMinDifference &&
            station.duff_moisture_code < dmcMaxDifference &&
            station.duff_moisture_code > dmcMinDifference
          ) {
            setShowTooltip(true)
          }
        }
      })
    }
  }

  const BASE_URL = 'https://wfapps.nrs.gov.bc.ca/pub/wfim/incidents/detail/'

  useEffect(() => {
    compareValues(props.stations, fireBehaviourResultStations)
  }, [props.rows])

  if (showTooltip) {
    return (
      <Paper className={classes.tooltip}>
        <div>
          <h4>Historical Fire Weather Pattern Detected</h4>
          <p>
            There were very similar weather conditions around McLean Lake for this{' '}
            <a href={BASE_URL + '2017/500637'}>incident.</a>
          </p>
        </div>
      </Paper>
    )
  }
  return (
    <Paper>
      <div className={classes.hiddenTooltip}>
        <h4>Historical Fire Weather Pattern Detected</h4>
        <p>
          There were very similar weather conditions around McLean Lake for this incident
        </p>
      </div>
    </Paper>
  )
}
