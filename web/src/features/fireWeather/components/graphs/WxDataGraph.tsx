import React, { useState } from 'react'
import { makeStyles } from '@material-ui/core/styles'
import moment from 'moment'

import { ModelSummary, ModelValue } from 'api/modelAPI'
import { ObservedValue } from 'api/observationAPI'
import { NoonForecastValue, ForecastSummary } from 'api/forecastAPI'
import WxDataGraphToggles from 'features/fireWeather/components/graphs/WxDataGraphToggles'
import { useGraphToggles } from 'features/fireWeather/components/graphs/useGraphToggles'
import TempRHGraph from 'features/fireWeather/components/graphs/TempRHGraph'
import PrecipGraph from 'features/fireWeather/components/graphs/PercipGraph'
import WindGraph from 'features/fireWeather/components/graphs/WindGraph'
import { formatDateInPST } from 'utils/date'

const useStyles = makeStyles({
  display: {
    paddingTop: 8
  }
})

interface Props {
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

  const noObservations = observedValues.length === 0
  const noModels = allModelValues.length === 0
  const noForecasts = allForecasts.length === 0
  const noBiasAdjModels =
    allModelValues.filter(
      v => v.bias_adjusted_temperature || v.bias_adjusted_relative_humidity
    ).length === 0
  const noHighResModels = allHighResModelValues.length === 0
  const noRegionalModels = allRegionalModelValues.length === 0

  const currDate = new Date()
  const initialXAxisRange: [string, string] = [
    formatDateInPST(moment(currDate).subtract(2, 'days').toDate()), // prettier-ignore
    formatDateInPST(moment(currDate).add(2, 'days').toDate()) // prettier-ignore
  ]
  const [sliderRange, setSliderRange] = useState(initialXAxisRange)
  const [toggleValues, setToggleValues] = useGraphToggles({
    showObservations: !noObservations,
    showForecasts: false,
    showModels: false,
    showBiasAdjModels: false,
    showHighResModels: !noHighResModels,
    showRegionalModels: false
  })

  if (
    noObservations &&
    noForecasts &&
    noModels &&
    noBiasAdjModels &&
    noHighResModels &&
    noRegionalModels
  ) {
    return null
  }

  return (
    <div className={classes.display}>
      <WxDataGraphToggles
        toggleValues={toggleValues}
        setToggleValues={setToggleValues}
        noObservations={noObservations}
        noForecasts={noForecasts}
        noModels={noModels}
        noBiasAdjModels={noBiasAdjModels}
        noHighResModels={noHighResModels}
        noRegionalModels={noRegionalModels}
      />

      <TempRHGraph
        toggleValues={toggleValues}
        observedValues={observedValues}
        forecastValues={allForecasts}
        forecastSummaries={forecastSummaries}
        gdpsValues={allModelValues}
        gdpsSummaries={modelSummaries}
        biasAdjGdpsValues={allModelValues}
        hrdpsValues={allHighResModelValues}
        hrdpsSummaries={highResModelSummaries}
        rdpsValues={allRegionalModelValues}
        rdpsSummaries={regionalModelSummaries}
      />

      <PrecipGraph
        currDate={currDate}
        sliderRange={sliderRange}
        setSliderRange={setSliderRange}
        toggleValues={toggleValues}
        observedValues={observedValues}
        forecastValues={allForecasts}
        gdpsModelValues={allModelValues}
        rdpsModelValues={allRegionalModelValues}
        hrdpsModelValues={allHighResModelValues}
      />

      <WindGraph
        currDate={currDate}
        sliderRange={sliderRange}
        setSliderRange={setSliderRange}
        toggleValues={toggleValues}
        observedValues={observedValues}
        gdpsModelValues={allModelValues}
        rdpsModelValues={allRegionalModelValues}
        hrdpsModelValues={allHighResModelValues}
      />
    </div>
  )
}

export default React.memo(WxDataGraph)
