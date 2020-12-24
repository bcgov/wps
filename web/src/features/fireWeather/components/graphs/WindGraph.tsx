import React from 'react'
import Plot from 'react-plotly.js'

import { ObservedValue } from 'api/observationAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'
import { Shape } from 'plotly.js'

export interface Props {
  toggleValues: ToggleValues
  observedValues: ObservedValue[]
}

/**
 * A working wind speed graph with Plotly, what's left and the most difficult thing to do
 * is to plot wind arrows in the graph. I have found some resources but couldn't find good examples :(
 * Clues about drawing arrows for wind direction
 * https://plotly.com/javascript/shapes/#basic-arbitrary-svg-paths (so far I feel like this is the way to go but it's going to be very difficult)
 * https://stackoverflow.com/a/64118466/11903963
 */

const WindGraph = (props: Props) => {
  const {
    observedValues,
    toggleValues: { showObservations }
  } = props
  const observedWindSpeeds = observedValues.map(v => v.wind_speed || NaN)
  const observedWindDirs = observedValues.map(v => v.wind_direction || NaN)
  const dates = observedValues.map(v => v.datetime)
  const maxWindSpd = Math.max(...observedWindSpeeds)
  const minWindSpd = Math.min(...observedWindSpeeds)
  const currDate = new Date()

  console.log(observedWindDirs)

  /**
   * Basic arrow shape (before any transformations)
   *  
   *   ^        "start"
   *  / \
   * /   \      "left_wing_tail" and "right_wing_tail"
   *   |
   *   |
   *   |        "arrow_tail"
   * 
   * 
   * */ 
  const start = [1, 3]
  const arrow_tail = [1, 0]
  const left_wing_tail = [0, 2]
  const right_wing_tail = [2, 2]

  const buildArrowPathString = function(arrowShape: number[][]): string {
    return `M${arrowShape[0][0]} ${arrowShape[0][1]} L${arrowShape[2][0]} ${arrowShape[2][1]} M${arrowShape[0][0]} ${arrowShape[0][1]} L${arrowShape[3][0]} ${arrowShape[3][1]} M${arrowShape[0][0]} ${arrowShape[0][1]} L${arrowShape[1][0]} ${arrowShape[1][1]}`
  }

  const rotateArrow = function(arrowShape: number[][], angle: number): number[][] {
    /**
     * Rotate arrow around stationary start location
     * 
     * Formula to rotate point (px, py) around point (ox, oy) by angle theta:
     * p'x = cos(theta)*(px-ox) - sin(theta)*(py-oy) + ox
     * p'y = sin(theta)*(px-ox) + cos(theta)*(py-oy) + oy
     */
    const start: number[] = arrowShape.slice(0,1).flat() // this is the point to rotate around
    const arrow_tail: number[] = arrowShape.slice(1,2).flat()
    const left_wing_tail: number[] = arrowShape.slice(2,3).flat()
    const right_wing_tail: number[] = arrowShape.slice(3,4).flat()
    const new_arrow_tail = [(arrow_tail[0] - start[0]) * Math.cos(angle) - Math.sin(angle) * (arrow_tail[1] - start[1]) + start[0], (arrow_tail[0] - start[0]) * Math.sin(angle) + Math.cos(angle) * (arrow_tail[1] - start[1]) + start[1]]
    const new_left_wing_tail = [(left_wing_tail[0] - start[0]) * Math.cos(angle) - Math.sin(angle) * (left_wing_tail[1] - start[1]) + start[0], (left_wing_tail[0] - start[0]) * Math.sin(angle) + Math.cos(angle) * (left_wing_tail[1] - start[1]) + start[1]]
    const new_right_wing_tail = [(right_wing_tail[0] - start[0]) * Math.cos(angle) - Math.sin(angle) * (right_wing_tail[1] - start[1] + start[0]), (right_wing_tail[0] - start[0]) * Math.sin(angle) + Math.cos(angle) * (right_wing_tail[1] - start[1]) + start[1]]
    return [start, new_arrow_tail, new_left_wing_tail, new_right_wing_tail]
  }

  const moveArrow = function(arrowShape: number[][], cx: number, cy: number): number[][] {
    const start: number[] = arrowShape.slice(0,1).flat()
    const arrow_tail: number[] = arrowShape.slice(1,2).flat()
    const left_wing_tail: number[] = arrowShape.slice(2,3).flat()
    const right_wing_tail: number[] = arrowShape.slice(3,4).flat()
    return [[start[0] + cx, start[1] + cy], [arrow_tail[0] + cx, arrow_tail[1] + cy], [left_wing_tail[0] + cx, left_wing_tail[1] + cy], [right_wing_tail[0] + cx, right_wing_tail[1] + cy]]
  }

  const calculateXOffset = function(data_index: number, intervals: number): number {
    return (750/intervals) * (data_index + 1)
  }

  const calculateYOffset = function(data_index: number): number {
    return 0
  }

  const rotatedArrows: Partial<Shape>[] = []
  for (var i = 0; i < observedWindDirs.length; i++) {
    const cx = calculateXOffset(i, observedWindDirs.length)
    const cy = calculateYOffset(i)
    var arrowShape = [start, arrow_tail, left_wing_tail, right_wing_tail]
    console.log(i)
    console.log('original arrowShape')
    console.log(arrowShape)
    arrowShape = moveArrow(arrowShape, cx, cy)
    console.log('move arrow')
    console.log(arrowShape)
    arrowShape = rotateArrow(arrowShape, observedWindDirs[i])
    console.log('rotate arrow')
    console.log(arrowShape)
    const pathString = buildArrowPathString(arrowShape)
    console.log(pathString)
    const path: Shape = {
      type: "path",
      path: pathString,
      visible: showObservations,
      layer: 'below',
      xref: 'paper',
      yref: 'paper',
      xanchor: 0,
      yanchor: 0,
      xsizemode: 'pixel',
      ysizemode: 'pixel',
      fillcolor: '#000000',
      opacity: 100,
      name: '',
      templateitemname: '',
      x0: NaN,
      y0: NaN,
      x1: NaN,
      y1: NaN,
      line: {
        color: showObservations ? '#000000' : 'transparent'
      }
    }
    rotatedArrows.push(path)
  }

  console.log(rotatedArrows)

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
          line: { color: showObservations ? '#057070' : 'transparent' },
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
          ...rotatedArrows
        ]
      }}
    />
  )
}

export default React.memo(WindGraph)
