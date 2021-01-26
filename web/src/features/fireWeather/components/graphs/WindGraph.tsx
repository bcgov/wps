/* eslint-disable @typescript-eslint/ban-ts-comment */
import React from 'react'
import Plot from 'react-plotly.js'

import { ObservedValue } from 'api/observationAPI'
import { ModelValue } from 'api/modelAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import {
  defaultLayoutConfig,
  findMaxNumber,
  findMinNumber,
  populateGraphDataForWind,
  populateNowLineData
} from 'features/fireWeather/components/graphs/plotlyHelper'

export interface Props {
  currDate: Date
  sliderRange: [string, string]
  toggleValues: ToggleValues
  observedValues: ObservedValue[]
  hrdpsModelValues: ModelValue[]
  rdpsModelValues: ModelValue[]
  gdpsModelValues: ModelValue[]
}

const observationLineColor = '#005f87'
const observationArrowColor = observationLineColor
const hrdpsLineColor = '#3ac417'
const hrdpsArrowColor = hrdpsLineColor
const rdpsLineColor = '#026200'
const rdpsArrowColor = rdpsLineColor
const gdpsLineColor = '#32e7e7'
const gdpsArrowColor = gdpsLineColor

const WindGraph = (props: Props) => {
  const {
    currDate,
    sliderRange,
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
    <div data-testid="wind-spd-dir-graph">
      <Plot
        style={{ width: '100%', height: '100%' }}
        config={{ responsive: true }}
        data={[
          nowLine,
          gdps.windSpdLine,
          rdps.windSpdLine,
          hrdps.windSpdLine,
          observation.windSpdLine
        ]}
        layout={{
          ...defaultLayoutConfig,
          title: {
            text: 'Wind Speed & Direction',
            yanchor: 'middle'
          },
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
          shapes: [
            ...observation.windDirArrows,
            ...gdps.windDirArrows,
            ...rdps.windDirArrows,
            ...hrdps.windDirArrows
          ]
        }}
      />
    </div>
  )
}

export default React.memo(WindGraph)
