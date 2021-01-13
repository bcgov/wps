/* eslint-disable @typescript-eslint/ban-ts-comment */
import React from 'react'
import Plot from 'react-plotly.js'
import moment from 'moment'

import { ObservedValue } from 'api/observationAPI'
import { ModelValue } from 'api/modelAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import { Shape } from 'plotly.js'

export interface Props {
  toggleValues: ToggleValues
  observedValues: ObservedValue[]
  hrdpsModelValues: ModelValue[]
  rdpsModelValues: ModelValue[]
  gdpsModelValues: ModelValue[]
}

interface WindSpeedValues {
  datetime: string
  wind_direction?: number | null
  wind_speed?: number | null
}

const observationLineColor = '#fb0058'
const observationArrowColor = observationLineColor
const gdpsLineColor = '#f56c9c'
const gdpsArrowColor = gdpsLineColor
const rdpsLineColor = '#ea6d0e'
const rdpsArrowColor = rdpsLineColor
const hrdpsLineColor = '#3ac417'
const hrdpsArrowColor = hrdpsLineColor

type Point = [number, number]

/**
 *   Basic arrow shape (before any transformations)
 *
 *              "front"
 *                 ^
 *                / \
 *   "leftEnd"   / | \   "rightEnd"
 *                 |
 *                 |
 *                 |
 *               "back"
 *
 */
const front: Point = [0, 8]
const back: Point = [0, -10]
const leftEnd: Point = [5, 0]
const rightEnd: Point = [-5, 0]
const arrowPoints = [front, back, leftEnd, rightEnd]

const buildArrowShapePath = (arrowShape: Point[]): string => {
  return `M${arrowShape[0][0]} ${arrowShape[0][1]} \
    L${arrowShape[2][0]} ${arrowShape[2][1]} \
    M${arrowShape[0][0]} ${arrowShape[0][1]} \
    L${arrowShape[3][0]} ${arrowShape[3][1]} \
    M${arrowShape[0][0]} ${arrowShape[0][1]} \
    L${arrowShape[1][0]} ${arrowShape[1][1]}`
}

const rotatePoints = (points: Point[], angle: number, cw = true): Point[] => {
  /**
   * https://academo.org/demos/rotation-about-point/
   * To rotate points around the origin,
   * to coordinates of the new point would be located at (x',y')
   *
   * x' = xcos(theta) - ysin(theta)
   * y' = ycos(theta) + xsin(theta)
   *
   * Where theta is the angle of rotation
   */

  // We need to rotate the arrow by 180 degrees (the degrees indiciate the origin of the wind,
  // not the direction)
  let theta = (Math.PI / 180) * ((angle + 180) % 360) // Turn the angle(number) into degree

  if (cw) {
    theta = -theta
  }

  return points.map(point => [
    point[0] * Math.cos(theta) - point[1] * Math.sin(theta),
    point[1] * Math.cos(theta) + point[0] * Math.sin(theta)
  ])
}

const createPath = (
  arrowShape: Point[],
  show: boolean,
  datetime: string,
  wind_speed: number,
  colour: string
): Partial<Shape> => {
  return {
    type: 'path',
    path: buildArrowShapePath(arrowShape),
    visible: show,
    layer: 'above',
    xref: 'x', // By setting a reference to the wind spd scale (x & y),
    yref: 'y', // we can position these arrows with wind spd values using xanchor & yanchor
    xsizemode: 'pixel', // https://plotly.com/javascript/reference/layout/shapes/#layout-shapes-items-shape-xsizemode
    ysizemode: 'pixel',
    xanchor: new Date(datetime).valueOf(),
    yanchor: wind_speed,
    line: {
      color: show ? colour : 'transparent'
    }
  }
}

const getLoopExtent = (
  layer: number,
  layoutLengths: number[]
): { start: number; end: number } => {
  // Element 0 is the vertical now bar, so we start at 1.
  let start = 1
  let end = start
  let i = 0
  // Iterate through the number of layers, moving the start and end index forward.
  do {
    start = end
    end += layoutLengths[i]
    i += 1
  } while (i <= layer)
  return {
    start,
    end
  }
}

const populateGraphData = (
  values: WindSpeedValues[],
  show: boolean,
  arrowColor: string
): {
  dates: Date[]
  windSpds: number[]
  windSpdsTexts: string[]
  windDirArrows: Partial<Shape>[]
} => {
  const dates: Date[] = []
  const windSpds: number[] = []
  const windSpdsTexts: string[] = []
  const windDirArrows: Partial<Shape>[] = []

  values.forEach(({ wind_direction, wind_speed, datetime }) => {
    if (wind_speed != null) {
      dates.push(new Date(datetime))
      windSpds.push(wind_speed)
      windSpdsTexts.push(wind_direction != null ? `${Math.round(wind_direction)}` : '-')

      if (wind_direction != null) {
        const arrowShape = rotatePoints(arrowPoints, wind_direction)
        const path = createPath(arrowShape, show, datetime, wind_speed, arrowColor)
        windDirArrows.push(path)
      }
    }
  })
  return { dates, windSpds, windSpdsTexts, windDirArrows }
}

const WindGraph = (props: Props) => {
  const {
    observedValues,
    gdpsModelValues,
    rdpsModelValues,
    hrdpsModelValues,
    toggleValues
  } = props
  const {
    showObservations,
    showModels,
    showRegionalModels,
    showHighResModels
  } = toggleValues

  const gdpsData = populateGraphData(gdpsModelValues, showModels, gdpsArrowColor)
  const rdpsData = populateGraphData(rdpsModelValues, showRegionalModels, rdpsArrowColor)
  const hrdpsData = populateGraphData(
    hrdpsModelValues,
    showHighResModels,
    hrdpsArrowColor
  )
  const observedData = populateGraphData(
    observedValues,
    showObservations,
    observationArrowColor
  )

  const maxWindSpd = Math.max(
    ...observedData.windSpds,
    ...gdpsData.windSpds,
    ...rdpsData.windSpds,
    ...hrdpsData.windSpds
  )
  const minWindSpd = Math.min(
    ...observedData.windSpds,
    ...gdpsData.windSpds,
    ...rdpsData.windSpds,
    ...hrdpsData.windSpds
  )

  const currDate = new Date()
  // Getting the axis range to persist between toggling different layers is problematic.
  // TODO: Add event handling that takes changes the range and persist it in the local store.
  const initialXAxisRange = [
    moment(currDate).subtract(2, 'days').toDate(), // prettier-ignore
    moment(currDate).add(2, 'days').toDate() // prettier-ignore
  ]

  return (
    <Plot
      style={{ width: '100%', height: '100%' }}
      onLegendClick={(event: Readonly<Plotly.LegendClickEvent>): boolean => {
        // We cannot group the shapes (arrows) with the legend (https://github.com/plotly/plotly.js/issues/98)
        // So we loop through the corresponding shapes (arrows) to toggle them on and off.
        // It's not very fast, but it works.
        // NOTE: The alternative would be to just make this function return false, thus disabling
        // toggling of layers using the legend.
        if (event.layout.shapes) {
          // Get the start and end positions of the arrows.
          const { start, end } = getLoopExtent(event.expandedIndex, [
            observedData.windSpds.length,
            gdpsData.windSpds.length,
            rdpsData.windSpds.length,
            hrdpsData.windSpds.length
          ])
          for (let i = start; i < end; ++i) {
            // Toggle visibility on the arrows.
            event.layout.shapes[i].visible = !event.layout.shapes[i].visible
          }
        }
        return true
      }}
      config={{ responsive: true }}
      data={[
        {
          x: observedData.dates,
          y: observedData.windSpds,
          name: 'Observed',
          mode: 'lines',
          type: 'scatter',
          showlegend: showObservations,
          line: {
            color: showObservations ? observationLineColor : 'transparent',
            width: 2
          },
          text: observedData.windSpdsTexts,
          hoverinfo: showObservations ? 'all' : 'skip',
          hovertemplate: showObservations
            ? 'Observation: %{y:.2f} km/h, %{text}°<extra></extra>'
            : ''
        },
        {
          x: gdpsData.dates,
          y: gdpsData.windSpds,
          name: 'GDPS',
          mode: 'lines',
          type: 'scatter',
          showlegend: showModels,
          line: {
            color: showModels ? gdpsLineColor : 'transparent',
            dash: 'longdash',
            width: 1
          },
          text: gdpsData.windSpdsTexts,
          hoverinfo: showModels ? 'all' : 'skip',
          hovertemplate: showModels ? 'GDPS: %{y:.2f} km/h, %{text}°<extra></extra>' : ''
        },
        {
          x: rdpsData.dates,
          y: rdpsData.windSpds,
          name: 'RDPS',
          mode: 'lines',
          type: 'scatter',
          showlegend: showRegionalModels,
          line: {
            color: showRegionalModels ? rdpsLineColor : 'transparent',
            width: 1,
            dash: 'dash'
          },
          text: rdpsData.windSpdsTexts,
          hoverinfo: showRegionalModels ? 'all' : 'skip',
          hovertemplate: showRegionalModels
            ? 'RDPS: %{y:.2f} km/h, %{text}°<extra></extra>'
            : ''
        },
        {
          x: hrdpsData.dates,
          y: hrdpsData.windSpds,
          name: 'HRDPS',
          mode: 'lines',
          type: 'scatter',
          showlegend: showHighResModels,
          line: {
            color: showHighResModels ? hrdpsLineColor : 'transparent',
            width: 1,
            dash: 'dot'
          },
          text: hrdpsData.windSpdsTexts,
          hoverinfo: showHighResModels ? 'all' : 'skip',
          hovertemplate: showHighResModels
            ? 'HRDPS: %{y:.2f} km/h, %{text}°<extra></extra>'
            : ''
        },
        {
          x: [currDate],
          y: [maxWindSpd + 0.6],
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
        autosize: true,
        title: {
          text: 'Wind speed & direction graph',
          yanchor: 'middle'
        },
        height: 600,
        margin: { pad: 10 },
        xaxis: {
          range: initialXAxisRange,
          rangeslider: {
            visible: true,
            bgcolor: '#dbdbdb',
            thickness: 0.1
          },
          rangeselector: {
            buttons: [
              {
                step: 'day',
                stepmode: 'backward',
                count: 1,
                label: '1d'
              },
              {
                step: 'day',
                stepmode: 'backward',
                count: 2,
                label: '2d'
              },
              { step: 'all' }
            ]
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
          {
            type: 'line',
            x0: currDate,
            y0: minWindSpd,
            x1: currDate,
            y1: maxWindSpd,
            line: {
              color: 'green',
              width: 1.5,
              dash: 'dot'
            },
            xref: 'x2',
            layer: 'below'
          },
          ...observedData.windDirArrows,
          ...gdpsData.windDirArrows,
          ...rdpsData.windDirArrows,
          ...hrdpsData.windDirArrows
        ]
      }}
    />
  )
}

export default React.memo(WindGraph)
