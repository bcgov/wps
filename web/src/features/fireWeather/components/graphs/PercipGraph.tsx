/* eslint-disable @typescript-eslint/ban-ts-comment */
import React from 'react'
import Plot from 'react-plotly.js'

import { ObservedValue } from 'api/observationAPI'
import { ModelValue } from 'api/modelAPI'
import { NoonForecastValue } from 'api/forecastAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import {
  findMaxNumber,
  layoutLegendConfig,
  populateGraphDataForPrecip,
  populateNowLineData
} from 'features/fireWeather/components/graphs/plotlyHelper'

const observedPrecipColor = '#a50b41'
const forecastPrecipColor = '#fb0058'
const gdpsPrecipColor = '#32e7e7'
const hrdpsPrecipColor = '#a017c2'
const rdpsPrecipColor = '#026200'

interface Props {
  currDate: Date
  sliderRange: [string, string]
  toggleValues: ToggleValues
  observedValues: ObservedValue[]
  forecastValues: NoonForecastValue[]
  hrdpsModelValues: ModelValue[]
  rdpsModelValues: ModelValue[]
  gdpsModelValues: ModelValue[]
}

const PrecipGraph = (props: Props) => {
  const {
    currDate,
    sliderRange,
    toggleValues,
    observedValues,
    forecastValues,
    gdpsModelValues,
    rdpsModelValues,
    hrdpsModelValues
  } = props

  const observation = populateGraphDataForPrecip(
    observedValues,
    'Observation',
    observedPrecipColor,
    toggleValues.showObservations
  )
  const forecast = populateGraphDataForPrecip(
    forecastValues,
    'Forecast',
    forecastPrecipColor,
    toggleValues.showForecasts
  )
  const hrdps = populateGraphDataForPrecip(
    hrdpsModelValues,
    'HRDPS',
    hrdpsPrecipColor,
    toggleValues.showHrdps
  )
  const gdps = populateGraphDataForPrecip(
    gdpsModelValues,
    'GDPS',
    gdpsPrecipColor,
    toggleValues.showGdps
  )
  const rdps = populateGraphDataForPrecip(
    rdpsModelValues,
    'RDPS',
    rdpsPrecipColor,
    toggleValues.showRdps
  )

  const maxY = findMaxNumber([
    observation.maxAccumPrecip,
    forecast.maxAccumPrecip,
    hrdps.maxAccumPrecip,
    gdps.maxAccumPrecip,
    rdps.maxAccumPrecip
  ])
  const y2Range = [0, maxY]
  const nowLine = populateNowLineData(currDate, y2Range[0], y2Range[1], 'y2')

  return (
    <Plot
      style={{ width: '100%', height: '100%' }}
      config={{ responsive: true }}
      data={[
        nowLine,
        gdps.accumPrecipsline,
        gdps.dailyPrecipsBar,
        rdps.accumPrecipsline,
        rdps.dailyPrecipsBar,
        hrdps.accumPrecipsline,
        hrdps.dailyPrecipsBar,
        forecast.accumPrecipsline,
        forecast.dailyPrecipsBar,
        observation.accumPrecipsline,
        observation.dailyPrecipsBar
      ]}
      layout={{
        dragmode: 'pan',
        autosize: true,
        title: {
          text: 'Daily Precipitation (with accumulated)',
          yanchor: 'middle'
        },
        height: 600,
        margin: { pad: 10 },
        xaxis: {
          range: sliderRange,
          rangeslider: {
            visible: true,
            bgcolor: '#dbdbdb',
            thickness: 0.1
          },
          hoverformat: '%a, %b %e', // https://github.com/d3/d3-3.x-api-reference/blob/master/Time-Formatting.md#format
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
          title: 'Daily Precipitation (mm/cm)',
          tickfont: { size: 14 },
          gridcolor: 'transparent',
          fixedrange: true,
          range: y2Range
        },
        yaxis2: {
          title: 'Accumulated Precipitation (mm/cm)',
          tickfont: { size: 14 },
          overlaying: 'y',
          side: 'right',
          fixedrange: true,
          range: y2Range
        },
        legend: layoutLegendConfig,
        barmode: 'group',
        bargap: 0.75,
        bargroupgap: 0.3
      }}
    />
  )
}

export default React.memo(PrecipGraph)
