import React from 'react'
import { useSelector } from 'react-redux'
import { Paper, Typography } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

import HourlyObservationsTable from 'features/fireWeather/components/HourlyObservationsTable'
import NoonForecastTable from 'features/fireWeather/components/NoonForecastTable'
import WxDataGraph from 'features/fireWeather/components/graphs/WxDataGraph'
import { ErrorBoundary } from 'components'
import { Station } from 'api/stationAPI'
import {
  selectObservations,
  selectModels,
  selectModelSummaries,
  selectForecasts,
  selectWxDataLoading,
  selectForecastSummaries,
  selectHighResModels,
  selectHighResModelSummaries
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
  requestedStations: Station[]
}

const WxDataDisplays = ({ requestedStations }: Props) => {
  const classes = useStyles()

  const { observationsByStation } = useSelector(selectObservations)
  const { allModelsByStation, noonModelsByStation } = useSelector(selectModels)
  const { modelSummariesByStation } = useSelector(selectModelSummaries)
  const { allNoonForecastsByStation } = useSelector(selectForecasts)
  const { forecastSummariesByStation } = useSelector(selectForecastSummaries)
  const { allHighResModelsByStation } = useSelector(selectHighResModels)
  const { highResModelSummariesByStation } = useSelector(selectHighResModelSummaries)
  const wxDataLoading = useSelector(selectWxDataLoading)

  return (
    <div className={classes.displays}>
      {!wxDataLoading &&
        requestedStations.map(s => {
          const observedValues = observationsByStation[s.code]
          const allModelValues = allModelsByStation[s.code]
          const modelSummaries = modelSummariesByStation[s.code]
          const noonModelValues = noonModelsByStation[s.code]
          const allForecasts = allNoonForecastsByStation[s.code]
          const forecastSummaries = forecastSummariesByStation[s.code]
          const allHighResModelValues = allHighResModelsByStation[s.code]
          const highResModelSummaries = highResModelSummariesByStation[s.code]
          const nothingToDisplay =
            !observedValues && !allForecasts && !allModelValues && !allHighResModelValues

          return (
            <Paper key={s.code} className={classes.paper} elevation={3}>
              <Typography className={classes.station} variant="subtitle1" component="div">
                Weather station: {`${s.name} (${s.code})`}
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
                  testId={`noon-models-table-${s.code}`}
                  title="Interpolated global model noon values (20:00 UTC): "
                  values={noonModelValues}
                />
              </ErrorBoundary>
              <ErrorBoundary>
                <NoonForecastTable
                  testId={`noon-forecasts-table-${s.code}`}
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
                />
              </ErrorBoundary>
            </Paper>
          )
        })}
    </div>
  )
}

export default React.memo(WxDataDisplays)
