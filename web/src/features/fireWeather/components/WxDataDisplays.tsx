import React from 'react'
import { useSelector } from 'react-redux'
import { Typography } from '@material-ui/core'
import { makeStyles } from '@material-ui/core/styles'

import ObservationTable from 'features/fireWeather/components/tables/ObservationTable'
import {
  NoonModelTable
} from 'features/fireWeather/components/tables/NoonWxValueTables'
import StationComparisonTable from 'features/fireWeather/components/tables/StationComparisonTable'
import NoonForecastTable from 'features/fireWeather/components/tables/NoonForecastTable'
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
  selectFireWeatherStations
} from 'app/rootReducer'
import { GeoJsonStation } from 'api/stationAPI'
import { ObservedValue } from 'api/observationAPI'
import { ModelSummary, ModelValue } from 'api/modelAPI'
import { ForecastSummary, NoonForecastValue } from 'api/forecastAPI'
import { SidePanelEnum } from 'features/fireWeather/components/SidePanel'
import { RedrawCommand } from 'features/map/Map'

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
  showTableView: string
  timeOfInterest: string
  expandedOrCollapsed?: RedrawCommand
  stationCodes: number[]
  wxDataLoading: boolean
  stationsByCode: Record<number, GeoJsonStation | undefined>
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

interface FragmentProps {
  view: string
  code: number
  noonOnlyGdpsModels: ModelValue[] | undefined
  observations: ObservedValue[] | undefined
  noonForecasts: NoonForecastValue[] | undefined
  station: GeoJsonStation
  expandedOrCollapsed?: { redraw: boolean }
  timeOfInterest: string
  noonForecastSummaries: ForecastSummary[] | undefined
  hrdpsModels: ModelValue[] | undefined
  hrdpsSummaries: ModelSummary[] | undefined
  rdpsModels: ModelValue[] | undefined
  rdpsSummaries: ModelSummary[] | undefined
  gdpsModels: ModelValue[] | undefined
  gdpsSummaries: ModelSummary[] | undefined
}

interface TableFragmentProps {
  code: number
  noonOnlyGdpsModels: ModelValue[] | undefined
  observations: ObservedValue[] | undefined
  noonForecasts: NoonForecastValue[] | undefined
}

const TableFragment = (props: TableFragmentProps) => {
  // Tables for a single station.
  const { code, noonOnlyGdpsModels, observations, noonForecasts } = props
  return (
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
          noonForecasts={noonForecasts}
          noonObservations={observations}
        />
      </ErrorBoundary>
    </React.Fragment>
  )
}

const SingleStationFragment = (props: FragmentProps) => {
  const {
    view,
    code,
    noonOnlyGdpsModels,
    observations,
    noonForecasts,
    station,
    timeOfInterest,
    expandedOrCollapsed,
    noonForecastSummaries,
    hrdpsModels,
    hrdpsSummaries,
    rdpsModels,
    rdpsSummaries,
    gdpsModels,
    gdpsSummaries
  } = props
  switch (view) {
    case SidePanelEnum.Tables:
      return (
        <TableFragment
          code={code}
          noonOnlyGdpsModels={noonOnlyGdpsModels}
          observations={observations}
          noonForecasts={noonForecasts}
        />
      )
    case SidePanelEnum.Graphs:
    default:
      return (
        <ErrorBoundary>
          <WxDataGraph
            station={station}
            timeOfInterest={timeOfInterest}
            expandedOrCollapsed={expandedOrCollapsed}
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
      )
  }
}

export const WxDataDisplays = React.memo(function _(props: WxDataDisplaysProps) {
  const classes = useStyles()

  return (
    <div className={classes.displays}>
      {props.wxDataLoading && 'Loading...'}

      {!props.wxDataLoading && props.showTableView === SidePanelEnum.Comparison && (
        <StationComparisonTable
          timeOfInterest={props.timeOfInterest}
          stationCodes={props.stationCodes}
          stationsByCode={props.stationsByCode}
          allNoonForecastsByStation={props.allNoonForecastsByStation}
          observationsByStation={props.observationsByStation}
          allHighResModelsByStation={props.allHighResModelsByStation}
          allRegionalModelsByStation={props.allRegionalModelsByStation}
          allModelsByStation={props.allModelsByStation}
        />
      )}

      {!props.wxDataLoading &&
        (props.showTableView === SidePanelEnum.Tables ||
          props.showTableView === SidePanelEnum.Graphs) &&
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
                {`${station.properties.name} (${station.properties.code})`}
              </Typography>
              {nothingToDisplay && (
                <Typography className={classes.noDataAvailable} variant="body2">
                  Data is not available.
                </Typography>
              )}
              <SingleStationFragment
                view={props.showTableView}
                code={code}
                noonOnlyGdpsModels={noonOnlyGdpsModels}
                station={station}
                timeOfInterest={props.timeOfInterest}
                expandedOrCollapsed={props.expandedOrCollapsed}
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
            </div>
          )
        })}
    </div>
  )
})

interface WxDataDisplaysWrapperProps {
  showTableView: string
  timeOfInterest: string
  expandedOrCollapsed?: { redraw: boolean }
  stationCodes: number[]
}

const WxDataDisplaysWrapper: React.FunctionComponent<WxDataDisplaysWrapperProps> = props => {
  const { stationsByCode } = useSelector(selectFireWeatherStations)
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
