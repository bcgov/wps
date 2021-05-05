import React, { useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { DateTime } from 'luxon'

import { GeoJsonStation } from 'api/stationAPI'
import { ModelSummary, ModelValue } from 'api/modelAPI'
import { ObservedValue } from 'api/observationAPI'
import { NoonForecastValue, ForecastSummary } from 'api/forecastAPI'
import WxDataGraphToggles from 'features/fireWeather/components/graphs/WxDataGraphToggles'
import { useGraphToggles } from 'features/fireWeather/components/graphs/useGraphToggles'
import PrecipitationGraph from 'features/fireWeather/components/graphs/PrecipitationGraph'
import WindGraph from 'features/fireWeather/components/graphs/WindGraph'
import TempRHGraph from 'features/fireWeather/components/graphs/TempRHGraph'
import { formatDateInPST } from 'utils/date'
import { RedrawCommand } from 'features/map/Map'

const useStyles = makeStyles({
  display: {
    paddingTop: 8
  }
})

interface Props {
  station: GeoJsonStation
  timeOfInterest: string
  expandedOrCollapsed?: RedrawCommand
  observations: ObservedValue[] | undefined
  noonForecasts: NoonForecastValue[] | undefined
  noonForecastSummaries: ForecastSummary[] | undefined
  hrdpsModels: ModelValue[] | undefined
  hrdpsSummaries: ModelSummary[] | undefined
  rdpsModels: ModelValue[] | undefined
  rdpsSummaries: ModelSummary[] | undefined
  gdpsModels: ModelValue[] | undefined
  gdpsSummaries: ModelSummary[] | undefined
}

const WxDataGraph = ({
  station,
  timeOfInterest,
  expandedOrCollapsed,
  observations = [],
  noonForecasts = [],
  noonForecastSummaries = [],
  hrdpsModels = [],
  hrdpsSummaries = [],
  rdpsModels = [],
  rdpsSummaries = [],
  gdpsModels = [],
  gdpsSummaries = []
}: Props) => {
  const classes = useStyles()

  const hasObservations = observations.length !== 0
  const hasModels = gdpsModels.length !== 0
  const hasForecasts = noonForecasts.length !== 0
  const hasBiasAdjModels =
    gdpsModels.filter(
      v => v.bias_adjusted_temperature || v.bias_adjusted_relative_humidity
    ).length !== 0
  const hasHighResModels = hrdpsModels.length !== 0
  const hasRegionalModels = rdpsModels.length !== 0

  /* Note: Plotly isn't updating its props in a correct way
   * (Plot component may mutate its layout and data props in response to user input, going against React rules) https://github.com/plotly/react-plotly.js#api-reference
   * This creates a weird/annoying behavior - Plotly modifying our state `sliderRange` directly,
   * therefore state `sliderRange` automatically keeps track of the range change triggered by user interactions.
   * (This is bad by the way since it makes impossible for us to capture the change of the state)
   */
  const initialXAxisRange: [string, string] = [
    formatDateInPST(DateTime.fromISO(timeOfInterest).minus({ days: 2 })), // prettier-ignore
    formatDateInPST(DateTime.fromISO(timeOfInterest).plus({ days: 2 })) // prettier-ignore
  ]
  const [sliderRange] = useState(initialXAxisRange)

  const [toggleValues, setToggleValues] = useGraphToggles({
    showObservations: hasObservations,
    showForecasts: hasForecasts,
    showHrdps: hasHighResModels,
    showRdps: false,
    showGdps: false,
    showBiasAdjGdps: false
  })

  if (
    !hasObservations &&
    !hasForecasts &&
    !hasModels &&
    !hasBiasAdjModels &&
    !hasHighResModels &&
    !hasRegionalModels
  ) {
    return null
  }

  return (
    <div className={classes.display}>
      <WxDataGraphToggles
        toggleValues={toggleValues}
        setToggleValues={setToggleValues}
        hasObservations={hasObservations}
        hasForecasts={hasForecasts}
        hasModels={hasModels}
        hasBiasAdjModels={hasBiasAdjModels}
        hasHighResModels={hasHighResModels}
        hasRegionalModels={hasRegionalModels}
      />

      <TempRHGraph
        station={station}
        timeOfInterest={timeOfInterest}
        expandedOrCollapsed={expandedOrCollapsed}
        sliderRange={sliderRange}
        toggleValues={toggleValues}
        observations={observations}
        noonForecasts={noonForecasts}
        NoonForecastSummaries={noonForecastSummaries}
        gdpsModels={gdpsModels}
        gdpsSummaries={gdpsSummaries}
        hrdpsModels={hrdpsModels}
        hrdpsSummaries={hrdpsSummaries}
        rdpsModels={rdpsModels}
        rdpsSummaries={rdpsSummaries}
      />

      <PrecipitationGraph
        station={station}
        timeOfInterest={timeOfInterest}
        expandedOrCollapsed={expandedOrCollapsed}
        sliderRange={sliderRange}
        toggleValues={toggleValues}
        observations={observations}
        noonForecasts={noonForecasts}
        hrdpsModels={hrdpsModels}
        gdpsModels={gdpsModels}
        rdpsModels={rdpsModels}
      />

      <WindGraph
        station={station}
        timeOfInterest={timeOfInterest}
        expandedOrCollapsed={expandedOrCollapsed}
        sliderRange={sliderRange}
        toggleValues={toggleValues}
        observations={observations}
        noonForecasts={noonForecasts}
        hrdpsModels={hrdpsModels}
        gdpsModels={gdpsModels}
        rdpsModels={rdpsModels}
      />
    </div>
  )
}

export default React.memo(WxDataGraph)
