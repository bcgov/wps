import React, { useState } from 'react'
import { useSelector } from 'react-redux'
import { Tab, Tabs, Typography } from '@material-ui/core'
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
import { TrendingUp, ViewHeadline } from '@material-ui/icons'

const useStyles = makeStyles({
  displays: {
    marginTop: 4
  },
  display: {
    marginBottom: 16
  },
  title: {
    fontSize: '1.2rem',
    paddingBottom: 8
  },
  noDataAvailable: {
    paddingBottom: 8
  }
})

interface WxDataDisplaysProps {
  timeOfInterest: string
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
  const [showTableView, toggleTableView] = useState(true)
  const [value, setTabNumber] = React.useState(0)

  const handleChange = (event: React.ChangeEvent<{}>, newValue: number) => {
    setTabNumber(newValue)
  }

  const classes = useStyles()

  return (
    <div className={classes.displays}>
      {props.wxDataLoading && 'Loading...'}

      {!props.wxDataLoading &&
        props.stationCodes.map(code => {
          const station = props.stationsByCode[code]
          if (!station) return null

          const observations = props.observationsByStation[code]
          const noonForecasts = props.allNoonForecastsByStation[code]
          const noonForecastSummaries = props.forecastSummariesByStation[code]
          const gdpsModels = props.allModelsByStation[code]
          const gdpsSummaries = props.modelSummariesByStation[code]
          const noonOnlyGdpsModels = props.noonModelsByStation[code]
          const hrdpsModels = props.allHighResModelsByStation[code]
          const hrdpsSummaries = props.highResModelSummariesByStation[code]
          const rdpsModels = props.allRegionalModelsByStation[code]
          const rdpsSummaries = props.regionalModelSummariesByStation[code]
          const nothingToDisplay =
            !observations && !noonForecasts && !gdpsModels && !hrdpsModels && !rdpsModels

          return (
            <div key={code} className={classes.display}>
              <Typography className={classes.title} variant="subtitle1" component="div">
                {`${station.name} (${station.code})`}
              </Typography>
              {nothingToDisplay && (
                <Typography className={classes.noDataAvailable} variant="body2">
                  Data is not available.
                </Typography>
              )}
              <div>
                <Tabs
                  value={value}
                  onChange={handleChange}
                  variant="fullWidth"
                  indicatorColor="secondary"
                  textColor="secondary"
                  aria-label="icon label tabs example"
                >
                  <Tab
                    icon={<ViewHeadline />}
                    label="Tables"
                    onClick={() => toggleTableView(true)}
                  />
                  <Tab
                    icon={<TrendingUp />}
                    label="Graphs"
                    onClick={() => toggleTableView(false)}
                  />
                </Tabs>
                {/* <Button
                  data-testid="table-data-tab-button"
                  id="table-data-tab-button"
                  variant="contained"
                  color="primary"
                  onClick={() => toggleTableView(true)}
                >
                  Tables
                </Button>
                <Button
                  data-testid="graph-data-tab-button"
                  id="graph-data-tab-button"
                  variant="contained"
                  color="primary"
                  onClick={() => toggleTableView(false)}
                >
                  Graphs
                </Button> */}
              </div>
              {showTableView ? (
                <React.Fragment>
                  <ErrorBoundary>
                    <ObservationTable
                      testId={`observations-table-${code}`}
                      title="Hourly observations in past 5 days: "
                      rows={observations}
                    />
                  </ErrorBoundary>
                  <ErrorBoundary>
                    <NoonModelTable
                      testId={`noon-gdps-table-${code}`}
                      title="Interpolated GDPS noon values: "
                      rows={noonOnlyGdpsModels}
                    />
                  </ErrorBoundary>
                  <ErrorBoundary>
                    <NoonForecastTable
                      testId={`noon-forecasts-table-${code}`}
                      title="Weather forecast noon values: "
                      rows={noonForecasts}
                    />
                  </ErrorBoundary>
                </React.Fragment>
              ) : (
                <React.Fragment>
                  <ErrorBoundary>
                    <WxDataGraph
                      station={station}
                      timeOfInterest={props.timeOfInterest}
                      observations={observations}
                      noonForecasts={noonForecasts}
                      noonForecastSummaries={noonForecastSummaries}
                      hrdpsModels={hrdpsModels}
                      hrdpsSummaries={hrdpsSummaries}
                      rdpsModels={rdpsModels}
                      rdpsSummaries={rdpsSummaries}
                      gdpsModels={gdpsModels}
                      gdpsSummaries={gdpsSummaries}
                    />
                  </ErrorBoundary>
                </React.Fragment>
              )}
            </div>
          )
        })}
    </div>
  )
})

interface WxDataDisplaysWrapperProps {
  timeOfInterest: string
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
