import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

import { ModelSummary, ModelValue } from 'api/modelAPI'
import { ObservedValue } from 'api/observationAPI'
import { NoonForecastValue, ForecastSummary } from 'api/forecastAPI'
import TempRHGraph from 'features/fireWeather/components/graphs/TempRHGraph'
import WxDataGraphToggles from 'features/fireWeather/components/graphs/WxDataGraphToggles'
import { useGraphToggles } from 'features/fireWeather/components/graphs/useGraphToggles'
import PrecipGraph from 'features/fireWeather/components/graphs/PrecipGraph'
import { highResModelValues, modelValues, regionalModelValues } from 'utils/storybook'

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
  const noModels = allModelValues.length === 0 && modelSummaries.length === 0
  const noForecasts = allForecasts.length === 0 && forecastSummaries.length === 0
  const noBiasAdjModels = allModelValues.length === 0
  const noHighResModels =
    allHighResModelValues.length === 0 && highResModelSummaries.length === 0
  const noRegionalModels =
    allRegionalModelValues.length === 0 && regionalModelSummaries.length === 0

  const [toggleValues, setToggleValues] = useGraphToggles({
    showObservations: !noObservations,
    showModels: false,
    showForecasts: false,
    showBiasAdjModels: false,
    showHighResModels: false,
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

  const {
    showObservations,
    showModels,
    showForecasts,
    showBiasAdjModels,
    showHighResModels,
    showRegionalModels
  } = toggleValues

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
        observedValues={showObservations ? observedValues : []}
        modelValues={showModels ? allModelValues : []}
        modelSummaries={showModels ? modelSummaries : []}
        forecastValues={showForecasts ? allForecasts : []}
        forecastSummaries={showForecasts ? forecastSummaries : []}
        biasAdjModelValues={showBiasAdjModels ? allModelValues : []}
        highResModelValues={showHighResModels ? allHighResModelValues : []}
        highResModelSummaries={showHighResModels ? highResModelSummaries : []}
        regionalModelValues={showRegionalModels ? allRegionalModelValues : []}
        regionalModelSummaries={showRegionalModels ? regionalModelSummaries : []}
      />

      <PrecipGraph
        toggleValues={toggleValues}
        observedValues={observedValues}
        forecastValues={allForecasts}
        gdpsModelValues={modelValues}
        rdpsModelValues={regionalModelValues}
        hrdpsModelValues={highResModelValues}
      />
    </div>
  )
}

export default React.memo(WxDataGraph)
