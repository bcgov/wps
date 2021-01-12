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

  let theta = (Math.PI / 180) * angle // Turn the angle(number) into degree

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

interface WindSpeedValues {
  datetime: string
  wind_direction?: number | null
  wind_speed?: number | null
}

const populateGraphData = (
  values: WindSpeedValues[],
  show: boolean,
  colour: string
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
        const path = createPath(arrowShape, show, datetime, wind_speed, colour)
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

  const gdpsData = populateGraphData(gdpsModelValues, showModels, '#ff0000')
  const rdpsData = populateGraphData(rdpsModelValues, showRegionalModels, '#00ff00')
  const hrdpsData = populateGraphData(hrdpsModelValues, showHighResModels, '#a017c2')
  const observedData = populateGraphData(observedValues, showObservations, '#0251a1')

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
  const initialXAxisRange = [
    moment(currDate).subtract(2, 'days').toDate(), // prettier-ignore
    moment(currDate).add(2, 'days').toDate() // prettier-ignore
  ]

  return (
    <Plot
      style={{ width: '100%', height: '100%' }}
      config={{ responsive: true }}
      data={[
        {
          x: observedData.dates,
          y: observedData.windSpds,
          name: 'Observation',
          mode: 'lines',
          type: 'scatter',
          showlegend: showObservations,
          line: { color: showObservations ? '#2491ff' : 'transparent' },
          text: observedData.windSpdsTexts,
          hovertemplate: showObservations
            ? 'Observation: %{y:.2f} km/h, %{text}°<extra></extra>'
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
        },
        {
          x: gdpsData.dates,
          y: gdpsData.windSpds,
          name: 'GDPS',
          mode: 'lines',
          type: 'scatter',
          showlegend: showModels,
          line: { color: showModels ? '#ff0000' : 'transparent' },
          text: gdpsData.windSpdsTexts,
          hovertemplate: 'GDPS: %{y:.2f} km/h, %{text}°<extra></extra>'
        },
        {
          x: rdpsData.dates,
          y: rdpsData.windSpds,
          name: 'RDPS',
          mode: 'lines',
          type: 'scatter',
          showlegend: showRegionalModels,
          line: { color: showRegionalModels ? '#00ff00' : 'transparent' },
          text: rdpsData.windSpdsTexts,
          hovertemplate: 'RDPS: %{y:.2f} km/h, %{text}°<extra></extra>'
        },
        {
          x: hrdpsData.dates,
          y: hrdpsData.windSpds,
          name: 'HRDPS',
          mode: 'lines',
          type: 'scatter',
          showlegend: showHighResModels,
          line: { color: showHighResModels ? '#a017c2' : 'transparent' },
          text: hrdpsData.windSpdsTexts,
          hovertemplate: 'HRDPS: %{y:.2f} km/h, %{text}°<extra></extra>'
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
