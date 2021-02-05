import React from 'react'
import { useSelector } from 'react-redux'
import { Paper, Typography } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

import ObservationTable from 'features/fireWeather/components/tables/ObservationTable'
import {
  NoonForecastTable,
  NoonModelTable
} from 'features/fireWeather/components/tables/NoonWxValueTables'
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
import { Station } from 'api/stationAPI'
import { ObservedValue } from 'api/observationAPI'
import { ModelSummary, ModelValue } from 'api/modelAPI'
import { ForecastSummary, NoonForecastValue } from 'api/forecastAPI'

const useStyles = makeStyles({
  displays: {
    marginTop: 16
  },
  paper: {
    paddingLeft: 18,
    paddingRight: 18,
    paddingBottom: 8,
    marginBottom: 20
  },
  station: {
    fontSize: '1.1rem',
    paddingTop: 10,
    paddingBottom: 8
  },
  noDataAvailable: {
    paddingBottom: 8
  }
})

interface WxDataDisplaysProps {
  timeOfInterest: Date
  stationCodes: number[]
  wxDataLoading: boolean
  stationsByCode: Record<number, Station | undefined>
  observationsByStation: Record<number, ObservedValue[] | undefined>
  allModelsByStation: Record<number, ModelValue[] | undefined>
  noonModelsByStation: Record<number, ModelValue[] | undefined>
  modelSummariesByStation: Record<number, ModelSummary[] | undefined>
  allNoonForecastsByStation: Record<number, NoonForecastValue[] | undefined>
  forecastSummariesByStation: Record<number, ForecastSummary[] | undefined>
  allHighResModelsByStation: Record<number, ModelValue[] | undefined>
  highResModelSummariesByStation: Record<number, ModelSummary[] | undefined>
  allRegionalModelsByStation: Record<number, ModelValue[] | undefined>
  regionalModelSummariesByStation: Record<number, ModelSummary[] | undefined>
}

export const WxDataDisplays = React.memo(function _(props: WxDataDisplaysProps) {
  const classes = useStyles()
  const { timeOfInterest } = props

  return (
    <div className={classes.displays}>
      {!props.wxDataLoading &&
        props.stationCodes.map(code => {
          const station = props.stationsByCode[code]
          if (!station) return null

          const observedValues = props.observationsByStation[code]
          const allModelValues = props.allModelsByStation[code]
          const modelSummaries = props.modelSummariesByStation[code]
          const noonModelValues = props.noonModelsByStation[code]
          const allForecasts = props.allNoonForecastsByStation[code]
          const forecastSummaries = props.forecastSummariesByStation[code]
          const allHighResModelValues = props.allHighResModelsByStation[code]
          const highResModelSummaries = props.highResModelSummariesByStation[code]
          const allRegionalModelValues = props.allRegionalModelsByStation[code]
          const regionalModelSummaries = props.regionalModelSummariesByStation[code]
          const nothingToDisplay =
            !observedValues &&
            !allForecasts &&
            !allModelValues &&
            !allHighResModelValues &&
            !allRegionalModelValues

          return (
            <Paper key={code} className={classes.paper} elevation={3}>
              <Typography className={classes.station} variant="subtitle1" component="div">
                Weather station: {`${station.name} (${station.code})`}
              </Typography>

              {nothingToDisplay && (
                <Typography className={classes.noDataAvailable} variant="body2">
                  Data is not available.
                </Typography>
              )}

              <ErrorBoundary>
                <ObservationTable
                  testId={`observations-table-${code}`}
                  title="Past 5 days of hourly observations from station: "
                  rows={observedValues}
                />
              </ErrorBoundary>

              <ErrorBoundary>
                <NoonModelTable
                  testId={`noon-gdps-table-${code}`}
                  title="Interpolated global model noon values: "
                  rows={noonModelValues}
                />
              </ErrorBoundary>

              <ErrorBoundary>
                <NoonForecastTable
                  testId={`noon-forecasts-table-${code}`}
                  title="Weather forecast noon values: "
                  rows={allForecasts}
                />
              </ErrorBoundary>

              <ErrorBoundary>
                <WxDataGraph
                  timeOfInterest={timeOfInterest}
                  station={station}
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
})

interface WxDataDisplaysWrapperProps {
  timeOfInterest: Date
  stationCodes: number[]
}

const WxDataDisplaysWrapper: React.FunctionComponent<WxDataDisplaysWrapperProps> = props => {
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
    <WxDataDisplays
      {...props}
      wxDataLoading={wxDataLoading}
      stationsByCode={stationsByCode}
      observationsByStation={observationsByStation}
      allModelsByStation={allModelsByStation}
      noonModelsByStation={noonModelsByStation}
      modelSummariesByStation={modelSummariesByStation}
      allNoonForecastsByStation={allNoonForecastsByStation}
      forecastSummariesByStation={forecastSummariesByStation}
      allHighResModelsByStation={allHighResModelsByStation}
      highResModelSummariesByStation={highResModelSummariesByStation}
      allRegionalModelsByStation={allRegionalModelsByStation}
      regionalModelSummariesByStation={regionalModelSummariesByStation}
    />
  )
}

export default WxDataDisplaysWrapper
