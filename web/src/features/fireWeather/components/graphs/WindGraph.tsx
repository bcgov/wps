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
  populateNowLineData,
  rangeSliderConfig
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
        onLegendClick={event => {
          // We cannot group the shapes (arrows) with the legend (https://github.com/plotly/plotly.js/issues/98)
          // So we loop through the corresponding shapes (arrows) to toggle them on and off.
          // It's not very fast, but it works.
          // NOTE: The alternative would be to just make this function return false, thus disabling
          // toggling of layers using the legend.

          const dataIndex = event.expandedIndex // determined by the order of the data array

          let clickedLegend: string | undefined = undefined

          switch (dataIndex) {
            case 1:
              clickedLegend = 'GDPS'
              break
            case 2:
              clickedLegend = 'RDPS'
              break
            case 3:
              clickedLegend = 'HRDPS'
              break
            case 4:
              clickedLegend = 'Observation'
              break

            default:
              break
          }

          event.layout.shapes?.forEach(shape => {
            if (clickedLegend && clickedLegend === shape.name) {
              shape.visible = !shape.visible
            }
          })

          return true
        }}
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
            title: 'Wind Speed (km/h)',
            tickfont: { size: 14 },
            fixedrange: true
          },
          shapes: [
            ...gdps.windDirArrows,
            ...rdps.windDirArrows,
            ...hrdps.windDirArrows,
            ...observation.windDirArrows
          ]
        }}
      />
    </div>
  )
}

export default React.memo(WindGraph)
