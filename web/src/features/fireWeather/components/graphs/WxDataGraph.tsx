import React, { useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import moment from 'moment'

import { ModelSummary, ModelValue } from 'api/modelAPI'
import { ObservedValue } from 'api/observationAPI'
import { NoonForecastValue, ForecastSummary } from 'api/forecastAPI'
import WxDataGraphToggles from 'features/fireWeather/components/graphs/WxDataGraphToggles'
import { useGraphToggles } from 'features/fireWeather/components/graphs/useGraphToggles'
import PrecipitationGraph from 'features/fireWeather/components/graphs/PrecipitationGraph'
import WindGraph from 'features/fireWeather/components/graphs/WindGraph'
import TempRHGraph from 'features/fireWeather/components/graphs/TempRHGraph'
import { formatDateInPST } from 'utils/date'
import { Station } from 'api/stationAPI'

const useStyles = makeStyles({
  display: {
    paddingTop: 8
  }
})

interface Props {
  station: Station
  observedValues: ObservedValue[] | undefined
  allModelValues: ModelValue[] | undefined
  modelSummaries: ModelSummary[] | undefined
  allForecasts: NoonForecastValue[] | undefined
  forecastSummaries: ForecastSummary[] | undefined
  allHighResModelValues: ModelValue[] | undefined
  highResModelSummaries: ModelSummary[] | undefined
  allRegionalModelValues: ModelValue[] | undefined
  regionalModelSummaries: ModelSummary[] | undefined
}

const WxDataGraph = ({
  station,
  observedValues = [],
  allModelValues = [],
  modelSummaries = [],
  allForecasts = [],
  forecastSummaries = [],
  allHighResModelValues = [],
  highResModelSummaries = [],
  allRegionalModelValues = [],
  regionalModelSummaries = []
}: Props) => {
  const classes = useStyles()

  const hasObservations = observedValues.length !== 0
  const hasModels = allModelValues.length !== 0
  const hasForecasts = allForecasts.length !== 0
  const hasBiasAdjModels =
    allModelValues.filter(
      v => v.bias_adjusted_temperature || v.bias_adjusted_relative_humidity
    ).length !== 0
  const hasHighResModels = allHighResModelValues.length !== 0
  const hasRegionalModels = allRegionalModelValues.length !== 0

  const currDate = new Date()

  /* Note: Plotly isn't updating its props in a correct way
   * (Plot component may mutate its layout and data props in response to user input, going against React rules) https://github.com/plotly/react-plotly.js#api-reference
   * This creates a weird/annoying behavior - Plotly modifying our state `sliderRange` directly,
   * therefore state `sliderRange` automatically keeps track of the range change triggered by user interactions.
   * (This is bad by the way since it makes impossible for us to capture the change of the state)
   */
  const initialXAxisRange: [string, string] = [
    formatDateInPST(moment(currDate).subtract(2, 'days').toDate()), // prettier-ignore
    formatDateInPST(moment(currDate).add(2, 'days').toDate()) // prettier-ignore
  ]
  const [sliderRange] = useState(initialXAxisRange)

  const [toggleValues, setToggleValues] = useGraphToggles({
    showObservations: hasObservations,
    showForecasts: false,
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
        currDate={currDate}
        sliderRange={sliderRange}
        toggleValues={toggleValues}
        observedValues={observedValues}
        forecastValues={allForecasts}
        forecastSummaries={forecastSummaries}
        gdpsValues={allModelValues}
        gdpsSummaries={modelSummaries}
        hrdpsValues={allHighResModelValues}
        hrdpsSummaries={highResModelSummaries}
        rdpsValues={allRegionalModelValues}
        rdpsSummaries={regionalModelSummaries}
      />

      <PrecipitationGraph
        station={station}
        currDate={currDate}
        sliderRange={sliderRange}
        toggleValues={toggleValues}
        observedValues={observedValues}
        forecastValues={allForecasts}
        hrdpsModelValues={allHighResModelValues}
        gdpsModelValues={allModelValues}
        rdpsModelValues={allRegionalModelValues}
      />

      <WindGraph
        station={station}
        currDate={currDate}
        sliderRange={sliderRange}
        toggleValues={toggleValues}
        observedValues={observedValues}
        hrdpsModelValues={allHighResModelValues}
        gdpsModelValues={allModelValues}
        rdpsModelValues={allRegionalModelValues}
      />
    </div>
  )
}

export default React.memo(WxDataGraph)
