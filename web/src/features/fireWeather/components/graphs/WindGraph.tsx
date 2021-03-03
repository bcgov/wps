/* eslint-disable @typescript-eslint/ban-ts-comment */
import React from 'react'
import Plot from 'react-plotly.js'

import { ObservedValue } from 'api/observationAPI'
import { ModelValue } from 'api/modelAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import { Station } from 'api/stationAPI'
import {
  getLayoutConfig,
  findMaxNumber,
  findMinNumber,
  populateGraphDataForWind,
  populateTimeOfInterestLineData,
  rangeSliderConfig
} from 'features/fireWeather/components/graphs/plotlyHelper'

export interface Props {
  station: Station
  timeOfInterest: string
  sliderRange: [string, string]
  toggleValues: ToggleValues
  observations: ObservedValue[]
  hrdpsModels: ModelValue[]
  rdpsModels: ModelValue[]
  gdpsModels: ModelValue[]
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
    station,
    timeOfInterest,
    sliderRange,
    toggleValues,
    observations,
    gdpsModels,
    rdpsModels,
    hrdpsModels
  } = props
  const { showObservations, showGdps, showRdps, showHrdps } = toggleValues

  const observationData = populateGraphDataForWind(
    observations,
    'Observation',
    showObservations,
    observationLineColor,
    observationArrowColor
  )
  const hrdpsData = populateGraphDataForWind(
    hrdpsModels,
    'HRDPS',
    showHrdps,
    hrdpsLineColor,
    hrdpsArrowColor
  )
  const rdpsData = populateGraphDataForWind(
    rdpsModels,
    'RDPS',
    showRdps,
    rdpsLineColor,
    rdpsArrowColor
  )
  const gdpsData = populateGraphDataForWind(
    gdpsModels,
    'GDPS',
    showGdps,
    gdpsLineColor,
    gdpsArrowColor
  )

  const maxWindSpd = findMaxNumber([
    observationData.maxWindSpd,
    gdpsData.maxWindSpd,
    rdpsData.maxWindSpd,
    hrdpsData.maxWindSpd
  ])
  const minWindSpd = findMinNumber([
    observationData.minWindSpd,
    gdpsData.minWindSpd,
    rdpsData.minWindSpd,
    hrdpsData.minWindSpd
  ])
  const timeOfInterestLine = populateTimeOfInterestLineData(
    timeOfInterest,
    minWindSpd,
    maxWindSpd
  )

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
          timeOfInterestLine,
          gdpsData.windSpdLine,
          rdpsData.windSpdLine,
          hrdpsData.windSpdLine,
          observationData.windSpdLine
        ]}
        layout={{
          ...getLayoutConfig(
            `Wind Speed & Direction - ${station.name} (${station.code})`
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
            title: 'Wind Speed (km/h)',
            tickfont: { size: 14 },
            fixedrange: true
          },
          shapes: [
            ...gdpsData.windDirArrows,
            ...rdpsData.windDirArrows,
            ...hrdpsData.windDirArrows,
            ...observationData.windDirArrows
          ]
        }}
      />
    </div>
  )
}

export default React.memo(WindGraph)
