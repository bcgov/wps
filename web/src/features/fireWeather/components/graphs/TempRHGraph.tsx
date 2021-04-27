/* eslint-disable @typescript-eslint/ban-ts-comment */
import React, { useEffect, useState } from 'react'
import Plot from 'react-plotly.js'

import { ObservedValue } from 'api/observationAPI'
import { ModelValue, ModelSummary } from 'api/modelAPI'
import { NoonForecastValue, ForecastSummary } from 'api/forecastAPI'
import { GeoJsonStation } from 'api/stationAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import {
  getLayoutConfig,
  populateGraphDataForTempAndRH,
  TempRHGraphProperties,
  populateTimeOfInterestLineData,
  rangeSliderConfig
} from 'features/fireWeather/components/graphs/plotlyHelper'
import { RedrawCommand } from 'features/map/Map'

const observedTempColor = '#4291FF'
const observedRHColor = '#EB5757'
const observedDewpointColor = '#949494'
const forecastTempColor = '#1200DE'
const forecastRHColor = '#910000'
const hrdpsTempColor = '#B86BFF'
const hrdpsRHColor = '#229B56'
const hrdpsTempPlumeColor = 'rgba(184, 107, 255, 0.2)'
const hrdpsRHPlumeColor = 'rgba(34, 155, 86, 0.2)'
const rdpsTempColor = '#FF64DD'
const rdpsRHColor = '#285777'
const rdpsTempPlumeColor = 'rgba(255, 100, 221, 0.2)'
const rdpsRHPlumeColor = 'rgba(40, 87, 119, 0.2)'
const gdpsTempColor = '#7556CA'
const gdpsRHColor = '#F2994A'
const gdpsTempPlumeColor = 'rgba(117, 86, 202, 0.2)'
const gdpsRHPlumeColor = 'rgba(242, 153, 74, 0.2)'
const biasGdpsTempColor = '#840DA2'
const biasGdpsRHColor = '#937D65'

interface Props {
  station: GeoJsonStation
  timeOfInterest: string
  expandedOrCollapsed?: RedrawCommand
  sliderRange: [string, string]
  toggleValues: ToggleValues
  observations: ObservedValue[]
  noonForecasts: NoonForecastValue[]
  NoonForecastSummaries: ForecastSummary[]
  hrdpsModels: ModelValue[]
  hrdpsSummaries: ModelSummary[]
  rdpsModels: ModelValue[]
  rdpsSummaries: ModelSummary[]
  gdpsModels: ModelValue[]
  gdpsSummaries: ModelSummary[]
}

const TempRHGraph = (props: Props) => {
  const {
    station,
    timeOfInterest,
    expandedOrCollapsed,
    sliderRange,
    toggleValues,
    observations,
    noonForecasts,
    NoonForecastSummaries,
    hrdpsModels,
    hrdpsSummaries,
    gdpsModels,
    gdpsSummaries,
    rdpsModels,
    rdpsSummaries
  } = props

  const obsGraphProperties: TempRHGraphProperties = {
    values: observations,
    tempName: 'Observed Temp',
    rhName: 'Observed RH',
    show: toggleValues.showObservations,
    symbol: 'circle', // https://plotly.com/javascript/reference/scatter/#scatter-marker-symbol
    dash: 'solid',
    tempColor: observedTempColor,
    rhColor: observedRHColor,
    dewpointName: 'Observed Dew Point',
    dewpointColor: observedDewpointColor
  }
  const observationData = populateGraphDataForTempAndRH(obsGraphProperties)

  const forecastGraphProperties: TempRHGraphProperties = {
    values: [...noonForecasts, ...NoonForecastSummaries],
    tempName: 'Forecast Temp',
    rhName: 'Forecash RH',
    show: toggleValues.showForecasts,
    symbol: 'pentagon',
    dash: 'solid',
    tempColor: forecastTempColor,
    rhColor: forecastRHColor
  }
  const forecastData = populateGraphDataForTempAndRH(forecastGraphProperties)

  const hrdpsGraphProperties: TempRHGraphProperties = {
    values: [...hrdpsModels, ...hrdpsSummaries],
    tempName: 'HRDPS Temp',
    rhName: 'HRDPS RH',
    show: toggleValues.showHrdps,
    symbol: 'square',
    dash: 'dash',
    tempColor: hrdpsTempColor,
    rhColor: hrdpsRHColor,
    tempPlumeColor: hrdpsTempPlumeColor,
    rhPlumeColor: hrdpsRHPlumeColor
  }
  const hrdpsData = populateGraphDataForTempAndRH(hrdpsGraphProperties)

  const gdpsGraphProperties: TempRHGraphProperties = {
    values: [...gdpsModels, ...gdpsSummaries],
    tempName: 'GDPS Temp',
    rhName: 'GDPS RH',
    show: toggleValues.showGdps,
    symbol: 'triangle-up',
    dash: 'dashdot',
    tempColor: gdpsTempColor,
    rhColor: gdpsRHColor,
    tempPlumeColor: gdpsTempPlumeColor,
    rhPlumeColor: gdpsRHPlumeColor
  }
  const gdpsData = populateGraphDataForTempAndRH(gdpsGraphProperties)

  const rdpsGraphProperties: TempRHGraphProperties = {
    values: [...rdpsModels, ...rdpsSummaries],
    tempName: 'RDPS Temp',
    rhName: 'RDPS RH',
    show: toggleValues.showRdps,
    symbol: 'diamond',
    dash: 'longdash',
    tempColor: rdpsTempColor,
    rhColor: rdpsRHColor,
    tempPlumeColor: rdpsTempPlumeColor,
    rhPlumeColor: rdpsRHPlumeColor
  }
  const rdpsData = populateGraphDataForTempAndRH(rdpsGraphProperties)

  const biasAdjGDPSGraphProperties: TempRHGraphProperties = {
    values: gdpsModels,
    tempName: 'Bias Adjusted GDPS Temp',
    rhName: 'Bias Adjusted GDPS RH',
    show: toggleValues.showBiasAdjGdps,
    symbol: 'star',
    dash: 'longdashdot',
    tempColor: biasGdpsTempColor,
    rhColor: biasGdpsRHColor
  }
  const biasAdjGdpsData = populateGraphDataForTempAndRH(biasAdjGDPSGraphProperties)

  const y2Range = [0, 102]
  const timeOfInterestLine = populateTimeOfInterestLineData(
    timeOfInterest,
    y2Range[0],
    y2Range[1],
    'y2'
  )

  // Update plotly revision to trigger re-drawing of the plot
  const setRevision = useState(0)[1]

  useEffect(() => {
    setRevision(revision => revision + 1)
  }, [expandedOrCollapsed, setRevision])

  return (
    <div id="temp-rh-graph" data-testid="temp-rh-graph">
      <Plot
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
        config={{ responsive: true }}
        data={[
          timeOfInterestLine,

          // Plumes
          gdpsData.rh5thLine,
          gdpsData.rh90thLine,
          gdpsData.temp5thLine,
          gdpsData.temp90thLine,
          rdpsData.rh5thLine,
          rdpsData.rh90thLine,
          rdpsData.temp5thLine,
          rdpsData.temp90thLine,
          hrdpsData.rh5thLine,
          hrdpsData.rh90thLine,
          hrdpsData.temp5thLine,
          hrdpsData.temp90thLine,

          // Lines & dots
          biasAdjGdpsData.biasAdjRHLine,
          biasAdjGdpsData.biasAdjTempLine,
          gdpsData.rhLine,
          gdpsData.tempLine,
          rdpsData.rhLine,
          rdpsData.tempLine,
          hrdpsData.rhLine,
          hrdpsData.tempLine,
          ...forecastData.tempVerticalLines,
          ...forecastData.rhVerticalLines,
          forecastData.rhDots,
          forecastData.tempDots,
          observationData.rhLine,
          observationData.tempLine,
          observationData.dewpointLine
        ]}
        layout={{
          ...getLayoutConfig(
            `Temperature, Dew Point & Relative Humidity - ${station.properties.name} (${station.properties.code})`
          ),
          xaxis: {
            range: sliderRange,
            rangeslider: rangeSliderConfig,
            hoverformat: '%I:00%p, %a, %b %e (PST)', // https://github.com/d3/d3-3.x-api-reference/blob/master/Time-Formatting.md#format
            tickfont: { size: 14 },
            type: 'date',
            dtick: 86400000.0 // Set the interval between ticks to one day: https://plotly.com/javascript/reference/#scatter-marker-colorbar-dtick
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
