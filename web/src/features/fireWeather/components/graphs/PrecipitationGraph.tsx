/* eslint-disable @typescript-eslint/ban-ts-comment */
import React, { useEffect, useState } from 'react'
import Plot from 'react-plotly.js'

import { ObservedValue } from 'api/observationAPI'
import { ModelValue } from 'api/modelAPI'
import { NoonForecastValue } from 'api/forecastAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import { GeoJsonStation } from 'api/stationAPI'
import {
  getLayoutConfig,
  findMaxNumber,
  populateGraphDataForPrecip,
  populateTimeOfInterestLineData,
  rangeSliderConfig
} from 'features/fireWeather/components/graphs/plotlyHelper'
import { RedrawCommand } from 'features/map/Map'

const observedPrecipColor = '#4291FF'
const forecastPrecipColor = '#1200DE'
const hrdpsPrecipColor = '#B86BFF'
const rdpsPrecipColor = '#FF64DD'
const gdpsPrecipColor = '#7556CA'

interface Props {
  station: GeoJsonStation
  timeOfInterest: string
  expandedOrCollapsed?: RedrawCommand
  sliderRange: [string, string]
  toggleValues: ToggleValues
  observations: ObservedValue[]
  noonForecasts: NoonForecastValue[]
  hrdpsModels: ModelValue[]
  rdpsModels: ModelValue[]
  gdpsModels: ModelValue[]
}

const PrecipitationGraph = (props: Props) => {
  const {
    station,
    timeOfInterest,
    expandedOrCollapsed,
    sliderRange,
    toggleValues,
    observations,
    noonForecasts,
    gdpsModels,
    rdpsModels,
    hrdpsModels
  } = props

  const observationData = populateGraphDataForPrecip(
    observations,
    'Observation',
    observedPrecipColor,
    toggleValues.showObservations
  )
  const forecastData = populateGraphDataForPrecip(
    noonForecasts,
    'Forecast',
    forecastPrecipColor,
    toggleValues.showForecasts
  )
  const hrdpsData = populateGraphDataForPrecip(
    hrdpsModels,
    'HRDPS',
    hrdpsPrecipColor,
    toggleValues.showHrdps
  )
  const gdpsData = populateGraphDataForPrecip(
    gdpsModels,
    'GDPS',
    gdpsPrecipColor,
    toggleValues.showGdps
  )
  const rdpsData = populateGraphDataForPrecip(
    rdpsModels,
    'RDPS',
    rdpsPrecipColor,
    toggleValues.showRdps
  )

  const maxY = findMaxNumber([
    observationData.maxAccumPrecip,
    forecastData.maxAccumPrecip,
    hrdpsData.maxAccumPrecip,
    gdpsData.maxAccumPrecip,
    rdpsData.maxAccumPrecip
  ])
  const y2Range = [0, maxY]
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
    <div data-testid="precipitation-graph">
      <Plot
        style={{ width: '100%', height: '100%' }}
        config={{ responsive: true }}
        data={[
          timeOfInterestLine,
          gdpsData.accumPrecipsline,
          gdpsData.dailyPrecipsBar,
          rdpsData.accumPrecipsline,
          rdpsData.dailyPrecipsBar,
          hrdpsData.accumPrecipsline,
          hrdpsData.dailyPrecipsBar,
          forecastData.accumPrecipsline,
          forecastData.dailyPrecipsBar,
          observationData.accumPrecipsline,
          observationData.dailyPrecipsBar
        ]}
        layout={{
          ...getLayoutConfig(
            `Daily Precipitation (with accumulated) - ${station.properties.name} (${station.properties.code})`
          ),
          barmode: 'group',
          bargap: 0.75,
          bargroupgap: 0.3,
          xaxis: {
            range: sliderRange,
            rangeslider: rangeSliderConfig,
            hoverformat: '%a, %b %e', // https://github.com/d3/d3-3.x-api-reference/blob/master/Time-Formatting.md#format
            tickfont: { size: 14 },
            type: 'date',
            dtick: 86400000.0 // Set the interval between ticks to one day: https://plotly.com/javascript/reference/#scatter-marker-colorbar-dtick
          },
          yaxis: {
            title: 'Daily Precipitation (mm)',
            tickfont: { size: 14 },
            gridcolor: 'transparent',
            fixedrange: true,
            range: y2Range
          },
          yaxis2: {
            title: 'Accumulated Precipitation (mm)',
            tickfont: { size: 14 },
            overlaying: 'y',
            side: 'right',
            fixedrange: true,
            range: y2Range
          }
        }}
      />
    </div>
  )
}

export default React.memo(PrecipitationGraph)
