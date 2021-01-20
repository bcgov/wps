/* eslint-disable @typescript-eslint/ban-ts-comment */
import React from 'react'
import Plot from 'react-plotly.js'
import { Data } from 'plotly.js'

import { ObservedValue } from 'api/observationAPI'
import { ModelValue, ModelSummary } from 'api/modelAPI'
import { NoonForecastValue, ForecastSummary } from 'api/forecastAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'

interface TempRHValue {
  datetime: string
  temperature?: number | null
  relative_humidity?: number | null
}

const populateGraphData = (
  values: TempRHValue[],
  tempName: string,
  rhName: string,
  show: boolean,
  tempColor: string,
  rhColor: string
) => {
  const dates: Date[] = []
  const temps: number[] = []
  const rhs: number[] = []

  values.forEach(({ datetime, temperature, relative_humidity }) => {
    if (temperature != null) {
      dates.push(new Date(datetime))
      temps.push(temperature)

      if (relative_humidity != null) {
        rhs.push(relative_humidity)
      }
    }
  })

  const tempsLine: Data = {
    x: dates,
    y: temps,
    name: tempName,
    mode: 'lines+markers',
    type: 'scatter',
    showlegend: show,
    line: {
      color: show ? tempColor : 'transparent',
      width: 2
    },
    hoverinfo: show ? 'all' : 'skip',
    hovertemplate: show ? `${tempName}: %{y:.2f} (°C)<extra></extra>` : ''
  }
  const rhsLine: Data = {
    x: dates,
    y: rhs,
    name: rhName,
    mode: 'lines+markers',
    yaxis: 'y2',
    type: 'scatter',
    showlegend: show,
    line: {
      color: show ? rhColor : 'transparent',
      width: 2
    },
    hoverinfo: show ? 'all' : 'skip',
    hovertemplate: show ? `${rhName}: %{y:.2f} (%)<extra></extra>` : ''
  }

  return { tempsLine, rhsLine, maxTemp: Math.max(...temps) }
}

const observedTempColor = '#fb0058'
const observedRHColor = '#057070'
const forecastTempColor = '#a50b41'
const forecastRHDotColor = '#17c4c4'
const gdpsTempColor = '#f56c9c'
const gdpsRHColor = '#32e7e7'
const biasdGdpsTempColor = '#e604d0'
const biasdGdpsRHColor = '#176bc4'
// const gdpsSummaryTempAreaColor = '#ff96aa'
// const gdpsSummaryRHAreaColor = '#94ffeb'
const hrdpsTempColor = '#a017c2'
const hrdpsRHColor = '#3ac417'
const hrdpsSummaryTempAreaColor = '#cba9d6'
const hrdpsSummaryRHAreaColor = '#b5f0a5'
const rdpsTempColor = '#ea6d0e'
const rdpsRHColor = '#026200'
const rdpsSummaryTempAreaColor = '#f48f41'
const rdpsSummaryRHAreaColor = '#2a8989'

interface Props {
  currDate: Date
  sliderRange: [string, string]
  setSliderRange: (range: [string, string]) => void
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
    currDate,
    sliderRange,
    setSliderRange,
    toggleValues,
    observedValues,
    forecastValues,
    gdpsValues,
    rdpsValues,
    hrdpsValues
  } = props

  const observation = populateGraphData(
    observedValues,
    'Observed Temp',
    'Observed RH',
    toggleValues.showObservations,
    observedTempColor,
    observedRHColor
  )
  const hrdps = populateGraphData(
    hrdpsValues,
    'HRDPS Temp',
    'HRDPS RH',
    toggleValues.showHighResModels,
    hrdpsTempColor,
    hrdpsRHColor
  )
  const gdps = populateGraphData(
    gdpsValues,
    'GDPS Temp',
    'GDPS RH',
    toggleValues.showModels,
    gdpsTempColor,
    gdpsRHColor
  )
  const rdps = populateGraphData(
    rdpsValues,
    'RDPS Temp',
    'RDPS RH',
    toggleValues.showRegionalModels,
    rdpsTempColor,
    rdpsRHColor
  )
  const maxY = Math.max(observation.maxTemp, hrdps.maxTemp, gdps.maxTemp, rdps.maxTemp)

  return (
    <Plot
      style={{ width: '100%', height: '100%' }}
      config={{ responsive: true }}
      onUpdate={e => {
        const updatedRange = e.layout.xaxis?.range as [string, string] | undefined
        if (updatedRange) {
          setSliderRange(updatedRange)
        }
      }}
      data={[
        observation.tempsLine,
        observation.rhsLine,
        hrdps.tempsLine,
        hrdps.rhsLine,
        gdps.tempsLine,
        gdps.rhsLine,
        rdps.tempsLine,
        rdps.rhsLine,
        {
          x: [currDate],
          y: [maxY * 1.02],
          mode: 'text',
          text: ['Now'],
          showlegend: false,
          hoverinfo: 'skip',
          textfont: { color: 'green', size: 15 },
          // a workaround to remove this from the slider: https://github.com/plotly/plotly.js/issues/2010#issuecomment-637697204
          xaxis: 'x2' // This moves trace to alternative xaxis(x2) which does not have a slider
        }
      ]}
      layout={{
        dragmode: 'pan',
        autosize: true,
        title: {
          text: 'Temperature & Relative Humidity',
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
          tickfont: { size: 14 },
          fixedrange: true
        },
        yaxis2: {
          title: 'Relative Humidity (%)',
          tickfont: { size: 14 },
          overlaying: 'y',
          side: 'right',
          gridcolor: 'transparent',
          range: [0, 100]
        },
        legend: {
          orientation: 'h',
          y: -0.45
        },
        shapes: [
          {
            type: 'line',
            x0: currDate,
            y0: 0,
            x1: currDate,
            y1: maxY,
            line: {
              color: 'green',
              width: 1.5,
              dash: 'dot'
            },
            xref: 'x2',
            layer: 'below'
          }
        ]
      }}
    />
  )
}

export default React.memo(TempRHGraph)
