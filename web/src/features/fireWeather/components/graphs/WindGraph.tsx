/* eslint-disable @typescript-eslint/ban-ts-comment */
import React from 'react'
import Plot from 'react-plotly.js'

import { ObservedValue } from 'api/observationAPI'
import { ModelValue } from 'api/modelAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import {
  findMaxNumber,
  findMinNumber,
  layoutLegendConfig,
  populateGraphDataForWind,
  populateNowLineData
} from 'features/fireWeather/components/graphs/plotlyHelper'

export interface Props {
  currDate: Date
  sliderRange: [string, string]
  setSliderRange: (range: [string, string]) => void
  toggleValues: ToggleValues
  observedValues: ObservedValue[]
  hrdpsModelValues: ModelValue[]
  rdpsModelValues: ModelValue[]
  gdpsModelValues: ModelValue[]
}

const observationLineColor = '#fb0058'
const observationArrowColor = observationLineColor
const gdpsLineColor = '#f56c9c'
const gdpsArrowColor = gdpsLineColor
const rdpsLineColor = '#ea6d0e'
const rdpsArrowColor = rdpsLineColor
const hrdpsLineColor = '#3ac417'
const hrdpsArrowColor = hrdpsLineColor

const WindGraph = (props: Props) => {
  const {
    currDate,
    sliderRange,
    setSliderRange,
    toggleValues,
    observedValues,
    gdpsModelValues,
    rdpsModelValues,
    hrdpsModelValues
  } = props
  const { showObservations, showGdps, showRdps, showHrdps } = toggleValues

  const observation = populateGraphDataForWind(
    observedValues,
    'Observation',
    showObservations,
    observationLineColor,
    observationArrowColor
  )
  const hrdps = populateGraphDataForWind(
    hrdpsModelValues,
    'HRDPS',
    showHrdps,
    hrdpsLineColor,
    hrdpsArrowColor
  )
  const rdps = populateGraphDataForWind(
    rdpsModelValues,
    'RDPS',
    showRdps,
    rdpsLineColor,
    rdpsArrowColor
  )
  const gdps = populateGraphDataForWind(
    gdpsModelValues,
    'GDPS',
    showGdps,
    gdpsLineColor,
    gdpsArrowColor
  )

  const maxWindSpd = findMaxNumber([
    observation.maxWindSpd,
    gdps.maxWindSpd,
    rdps.maxWindSpd,
    hrdps.maxWindSpd
  ])
  const minWindSpd = findMinNumber([
    observation.minWindSpd,
    gdps.minWindSpd,
    rdps.minWindSpd,
    hrdps.minWindSpd
  ])
  const nowLine = populateNowLineData(currDate, minWindSpd, maxWindSpd)

  return (
    <Plot
      style={{ width: '100%', height: '100%' }}
      config={{ responsive: true }}
      onUpdate={e => {
        const updatedRange = e.layout.xaxis?.range as [string, string] | undefined
        if (updatedRange) {
          // setSliderRange(updatedRange)
        }
      }}
      data={[
        nowLine,
        gdps.windSpdLine,
        rdps.windSpdLine,
        hrdps.windSpdLine,
        observation.windSpdLine
      ]}
      layout={{
        dragmode: 'pan',
        autosize: true,
        title: {
          text: 'Wind Speed & Direction',
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
          title: 'Wind Speed (km/h)',
          tickfont: { size: 14 },
          fixedrange: true
        },
        legend: layoutLegendConfig,
        shapes: [
          ...observation.windDirArrows,
          ...gdps.windDirArrows,
          ...rdps.windDirArrows,
          ...hrdps.windDirArrows
        ]
      }}
    />
  )
}

export default React.memo(WindGraph)
