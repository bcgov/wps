import React from 'react'
import Plot from 'react-plotly.js'

import { ObservedValue } from 'api/observationAPI'
import { ToggleValues } from 'features/fireWeather/components/graphs/useGraphToggles'

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
  const dates = observedValues.map(v => v.datetime)
  const maxWindSpd = Math.max(...observedWindSpeeds)
  const minWindSpd = Math.min(...observedWindSpeeds)
  const currDate = new Date()

  return (
    <Plot
      style={{ width: '100%', height: '100%' }}
      config={{ responsive: true }}
      data={[
        {
          x: dates,
          y: observedWindSpeeds,
          mode: 'lines+markers',
          type: 'scatter',
          showlegend: false,
          marker: {
            color: showObservations ? '#057070' : 'transparent',
            symbol: 'circle' // https://github.com/plotly/plotly.js/blob/master/src/components/drawing/symbol_defs.js
          },
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
          }
        ]
      }}
    />
  )
}

export default React.memo(WindGraph)
