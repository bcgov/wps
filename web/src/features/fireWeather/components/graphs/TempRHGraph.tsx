/* eslint-disable @typescript-eslint/ban-ts-comment */
import React from 'react'
import Plot from 'react-plotly.js'

import { ObservedValue } from 'api/observationAPI'
import { ModelValue, ModelSummary } from 'api/modelAPI'
import { NoonForecastValue, ForecastSummary } from 'api/forecastAPI'
import { Station } from 'api/stationAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import {
  getLayoutConfig,
  populateGraphDataForTempAndRH,
  populateTimeOfInterestLineData,
  rangeSliderConfig
} from 'features/fireWeather/components/graphs/plotlyHelper'

const observedTempColor = '#fb0058'
const observedRHColor = '#005f87'
const forecastTempColor = '#a50b41'
const forecastRHColor = '#17c4c4'
const hrdpsTempColor = '#a017c2'
const hrdpsRHColor = '#3ac417'
const hrdpsTempPlumeColor = 'rgba(203, 169, 214, 0.4)'
const hrdpsRHPlumeColor = 'rgba(181, 240, 165, 0.4)'
const rdpsTempColor = '#ea6d0e'
const rdpsRHColor = '#026200'
const rdpsTempPlumeColor = 'rgba(244, 143, 65, 0.4)'
const rdpsRHPlumeColor = 'rgba(42, 137, 137, 0.4)'
const gdpsTempColor = '#f56c9c'
const gdpsRHColor = '#32e7e7'
const gdpsTempPlumeColor = 'rgba(255, 150, 169, 0.4)'
const gdpsRHPlumeColor = 'rgba(148, 255, 235, 0.4)'
const biasdGdpsTempColor = '#e604d0'
const biasdGdpsRHColor = '#176bc4'

interface Props {
  station: Station
  timeOfInterest: Date
  sliderRange: [string, string]
  toggleValues: ToggleValues
  observedValues: ObservedValue[]
  forecastValues: NoonForecastValue[]
  forecastSummaries: ForecastSummary[]
  hrdpsValues: ModelValue[]
  hrdpsSummaries: ModelSummary[]
  rdpsValues: ModelValue[]
  rdpsSummaries: ModelSummary[]
  gdpsValues: ModelValue[]
  gdpsSummaries: ModelSummary[]
}

const TempRHGraph = (props: Props) => {
  const {
    station,
    timeOfInterest,
    sliderRange,
    toggleValues,
    observedValues,
    forecastValues,
    forecastSummaries,
    hrdpsValues,
    hrdpsSummaries,
    gdpsValues,
    gdpsSummaries,
    rdpsValues,
    rdpsSummaries
  } = props

  const observation = populateGraphDataForTempAndRH(
    observedValues,
    'Observed Temp',
    'Observed RH',
    toggleValues.showObservations,
    'circle', // https://plotly.com/javascript/reference/scatter/#scatter-marker-symbol
    'solid',
    observedTempColor,
    observedRHColor
  )
  const forecast = populateGraphDataForTempAndRH(
    [...forecastValues, ...forecastSummaries],
    'Forecast Temp',
    'Forecast RH',
    toggleValues.showForecasts,
    'pentagon',
    'solid',
    forecastTempColor,
    forecastRHColor
  )
  const hrdps = populateGraphDataForTempAndRH(
    [...hrdpsValues, ...hrdpsSummaries],
    'HRDPS Temp',
    'HRDPS RH',
    toggleValues.showHrdps,
    'square',
    'dash',
    hrdpsTempColor,
    hrdpsRHColor,
    hrdpsTempPlumeColor,
    hrdpsRHPlumeColor
  )
  const gdps = populateGraphDataForTempAndRH(
    [...gdpsValues, ...gdpsSummaries],
    'GDPS Temp',
    'GDPS RH',
    toggleValues.showGdps,
    'triangle-up',
    'dashdot',
    gdpsTempColor,
    gdpsRHColor,
    gdpsTempPlumeColor,
    gdpsRHPlumeColor
  )
  const rdps = populateGraphDataForTempAndRH(
    [...rdpsValues, ...rdpsSummaries],
    'RDPS Temp',
    'RDPS RH',
    toggleValues.showRdps,
    'diamond',
    'longdash',
    rdpsTempColor,
    rdpsRHColor,
    rdpsTempPlumeColor,
    rdpsRHPlumeColor
  )
  const biasAdjGdps = populateGraphDataForTempAndRH(
    gdpsValues,
    'Bias Adjusted GDPS Temp',
    'Bias Adjusted GDPS RH',
    toggleValues.showBiasAdjGdps,
    'star',
    'longdashdot',
    biasdGdpsTempColor,
    biasdGdpsRHColor
  )

  const y2Range = [0, 102]
  const timeOfInterestLine = populateTimeOfInterestLineData(
    timeOfInterest,
    y2Range[0],
    y2Range[1],
    'y2'
  )

  return (
    <div data-testid="temp-rh-graph">
      <Plot
        style={{ width: '100%', height: '100%' }}
        config={{ responsive: true }}
        data={[
          timeOfInterestLine,

          // Plumes
          gdps.rh5thLine,
          gdps.rh90thLine,
          gdps.temp5thLine,
          gdps.temp90thLine,
          rdps.rh5thLine,
          rdps.rh90thLine,
          rdps.temp5thLine,
          rdps.temp90thLine,
          hrdps.rh5thLine,
          hrdps.rh90thLine,
          hrdps.temp5thLine,
          hrdps.temp90thLine,

          // Lines & dots
          biasAdjGdps.biasAdjRHLine,
          biasAdjGdps.biasAdjTempLine,
          gdps.rhLine,
          gdps.tempLine,
          rdps.rhLine,
          rdps.tempLine,
          hrdps.rhLine,
          hrdps.tempLine,
          ...forecast.tempVerticalLines,
          ...forecast.rhVerticalLines,
          forecast.rhDots,
          forecast.tempDots,
          observation.rhLine,
          observation.tempLine
        ]}
        layout={{
          ...getLayoutConfig(
            `Temperature & Relative Humidity - ${station.name} (${station.code})`
          ),
          xaxis: {
            range: sliderRange,
            rangeslider: rangeSliderConfig,
            hoverformat: '%I:00%p, %a, %b %e', // https://github.com/d3/d3-3.x-api-reference/blob/master/Time-Formatting.md#format
            tickfont: { size: 14 },
            type: 'date',
            dtick: 86400000.0 // Set the interval between ticks to one day: https://plotly.com/javascript/reference/#scatter-marker-colorbar-dtick
          },
          xaxis2: {
            type: 'date',
            showticklabels: false,
            // @ts-expect-error
            matches: 'x', // Important for slider to work properly for all traces
            overlaying: 'x' // Important for hover to work properly for all traces
          },
          yaxis: {
            title: 'Temperature (°C)',
            tickfont: { size: 14 }
          },
          yaxis2: {
            title: 'Relative Humidity (%)',
            tickfont: { size: 14 },
            overlaying: 'y',
            side: 'right',
            gridcolor: 'transparent',
            range: y2Range
          }
        }}
      />
    </div>
  )
}

export default React.memo(TempRHGraph)
