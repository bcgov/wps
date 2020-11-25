import React from 'react'
import { useSelector } from 'react-redux'
import { Paper, Typography } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

import HourlyObservationsTable from 'features/fireWeather/components/HourlyObservationsTable'
import NoonForecastTable from 'features/fireWeather/components/NoonForecastTable'
import WxDataGraph from 'features/fireWeather/components/graphs/WxDataGraph'
import { ErrorBoundary } from 'components'
import {
  selectObservations,
  selectModels,
  selectModelSummaries,
  selectForecasts,
  selectWxDataLoading,
  selectForecastSummaries,
  selectHighResModels,
  selectHighResModelSummaries,
  selectRegionalModels,
  selectRegionalModelSummaries,
  selectStations
} from 'app/rootReducer'

const useStyles = makeStyles({
  displays: {
    marginTop: 16
  },
  paper: {
    paddingLeft: 16,
    paddingRight: 16,
    marginBottom: 20
  },
  station: {
    fontSize: '1.1rem',
    paddingTop: 8,
    paddingBottom: 8
  },
  noDataAvailable: {
    paddingBottom: 8
  }
})

interface Props {
  stationCodes: number[]
}

const WxDataDisplays = ({ stationCodes }: Props) => {
  const classes = useStyles()

  const { stationsByCode } = useSelector(selectStations)
  const { observationsByStation } = useSelector(selectObservations)
  const { allModelsByStation, noonModelsByStation } = useSelector(selectModels)
  const { modelSummariesByStation } = useSelector(selectModelSummaries)
  const { allNoonForecastsByStation } = useSelector(selectForecasts)
  const { forecastSummariesByStation } = useSelector(selectForecastSummaries)
  const { allHighResModelsByStation } = useSelector(selectHighResModels)
  const { highResModelSummariesByStation } = useSelector(selectHighResModelSummaries)
  const { allRegionalModelsByStation } = useSelector(selectRegionalModels)
  const { regionalModelSummariesByStation } = useSelector(selectRegionalModelSummaries)
  const wxDataLoading = useSelector(selectWxDataLoading)

  return (
    <div className={classes.displays}>
      {!wxDataLoading &&
        stationCodes.map(code => {
          const station = stationsByCode[code]
          if (!station) return null

          const observedValues = observationsByStation[code]
          const allModelValues = allModelsByStation[code]
          const modelSummaries = modelSummariesByStation[code]
          const noonModelValues = noonModelsByStation[code]
          const allForecasts = allNoonForecastsByStation[code]
          const forecastSummaries = forecastSummariesByStation[code]
          const allHighResModelValues = allHighResModelsByStation[code]
          const highResModelSummaries = highResModelSummariesByStation[code]
          const allRegionalModelValues = allRegionalModelsByStation[code]
          const regionalModelSummaries = regionalModelSummariesByStation[code]
          const nothingToDisplay =
            !observedValues &&
            !allForecasts &&
            !allModelValues &&
            !allHighResModelValues &&
            !allRegionalModelValues

          return (
            <Paper key={code} className={classes.paper} elevation={3}>
              <Typography className={classes.station} variant="subtitle1" component="div">
                Weather station: {station ? `${station.name} (${code})` : code}
              </Typography>
              {nothingToDisplay && (
                <Typography className={classes.noDataAvailable} variant="body2">
                  Data is not available.
                </Typography>
              )}
              <ErrorBoundary>
                <HourlyObservationsTable
                  title="Past 5 days of hourly observations from station: "
                  values={observedValues}
                />
              </ErrorBoundary>
              <ErrorBoundary>
                <NoonForecastTable
                  testId={`noon-models-table-${code}`}
                  title="Interpolated global model noon values (20:00 UTC): "
                  values={noonModelValues}
                />
              </ErrorBoundary>
              <ErrorBoundary>
                <NoonForecastTable
                  testId={`noon-forecasts-table-${code}`}
                  title="Weather forecast noon values (20:00 UTC): "
                  values={allForecasts}
                />
              </ErrorBoundary>
              <ErrorBoundary>
                <WxDataGraph
                  observedValues={observedValues}
                  allModelValues={allModelValues}
                  modelSummaries={modelSummaries}
                  allForecasts={allForecasts}
                  forecastSummaries={forecastSummaries}
                  allHighResModelValues={allHighResModelValues}
                  highResModelSummaries={highResModelSummaries}
                  allRegionalModelValues={allRegionalModelValues}
                  regionalModelSummaries={regionalModelSummaries}
                />
              </ErrorBoundary>
            </Paper>
          )
        })}
    </div>
  )
}

export default React.memo(WxDataDisplays)
