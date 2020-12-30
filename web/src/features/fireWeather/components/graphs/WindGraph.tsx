import React from 'react'
import Plot from 'react-plotly.js'

import { ObservedValue } from 'api/observationAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import { Shape } from 'plotly.js'

export interface Props {
  toggleValues: ToggleValues
  observedValues: ObservedValue[]
}

type Point = [number, number]

/**
 *   Basic arrow shape (before any transformations)
 *
 *              "front"
 *                 ^
 *                / \
 *   "leftEnd"   /   \   "rightEnd"
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

const buildArrowShapeDParam = (arrowShape: Point[]): string => {
  return `M${arrowShape[0][0]} ${arrowShape[0][1]} \
    L${arrowShape[2][0]} ${arrowShape[2][1]} \
    M${arrowShape[0][0]} ${arrowShape[0][1]} \
    L${arrowShape[3][0]} ${arrowShape[3][1]} \
    M${arrowShape[0][0]} ${arrowShape[0][1]} \
    L${arrowShape[1][0]} ${arrowShape[1][1]}`
}

const rotatePointsByAngle = (points: Point[], angle: number, cw = true): Point[] => {
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

  let theta = (Math.PI / 180) * angle // Translate the angle into degree

  if (cw) {
    theta = -theta
  }

  return points.map(point => [
    point[0] * Math.cos(theta) - point[1] * Math.sin(theta),
    point[1] * Math.cos(theta) + point[0] * Math.sin(theta)
  ])
}

const WindGraph = (props: Props) => {
  const { observedValues, toggleValues } = props
  const { showObservations } = toggleValues
  const observedWindSpeeds = observedValues.map(v => v.wind_speed || NaN)
  const dates = observedValues.map(v => new Date(v.datetime))
  const maxWindSpd = Math.max(...observedWindSpeeds)
  const minWindSpd = Math.min(...observedWindSpeeds)
  const currDate = new Date()

  const observedWindDirArrows: Partial<Shape>[] = []
  observedValues.forEach(({ wind_direction, wind_speed, datetime }) => {
    if (!wind_speed || !wind_direction) return

    const arrowShape = rotatePointsByAngle(arrowPoints, wind_direction)
    const dParameter = buildArrowShapeDParam(arrowShape)

    const path: Partial<Shape> = {
      type: 'path',
      path: dParameter,
      visible: showObservations,
      layer: 'above',
      xref: 'x',
      yref: 'y',
      xsizemode: 'pixel', // https://plotly.com/javascript/reference/layout/shapes/#layout-shapes-items-shape-xsizemode
      ysizemode: 'pixel',
      xanchor: new Date(datetime).valueOf(),
      yanchor: wind_speed,
      templateitemname: 'hmm',
      name: 'name',
      line: {
        color: showObservations ? '#0251a1' : 'transparent'
      }
    }

    observedWindDirArrows.push(path)
  })

  return (
    <Plot
      style={{ width: '100%', height: '100%' }}
      config={{ responsive: true }}
      data={[
        {
          x: dates,
          y: observedWindSpeeds,
          mode: 'lines',
          type: 'scatter',
          showlegend: false,
          line: { color: showObservations ? '#0080ff' : 'transparent' },
          connectgaps: true, // to fill the possible gap from null values
          hovertemplate: 'Observed Wind Spd: %{y:.2f} (km/h) <extra></extra>'
        },
        {
          x: [currDate],
          y: [maxWindSpd + 0.6],
          mode: 'text',
          text: ['Now'],
          showlegend: false,
          hoverinfo: 'none',
          textfont: { color: 'green', size: 15 }
        }
      ]}
      layout={{
        autosize: true,
        title: {
          text: 'Wind speed & direction graph',
          yanchor: 'middle'
        },
        height: 450,
        margin: { pad: 10 },
        xaxis: {
          tickfont: { size: 14 },
          type: 'date',
          dtick: 86400000.0 // to set the interval between ticks to one day: https://plotly.com/javascript/reference/#scatter-marker-colorbar-dtick
        },
        yaxis: {
          title: 'Wind Speed (km/h)',
          tickfont: { size: 14 }
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
            }
          },
          ...observedWindDirArrows
        ]
      }}
    />
  )
}

export default React.memo(WindGraph)
