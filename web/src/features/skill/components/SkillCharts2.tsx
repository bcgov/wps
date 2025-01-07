import React from 'react'
import Plot from 'react-plotly.js'
import * as Plotly from 'plotly.js'
import { MORECAST_MODEL_COLORS } from 'app/theme'

const SkillCharts2 = () => {
  const hrdps: Plotly.Data = {
    x: [0.2, -0.9, 0.6, -0.1, 2.5, 0.8, -0.3, 0.7, 0.2, 1.0],
    type: 'box',
    name: 'HRDPS',
    marker: { color: MORECAST_MODEL_COLORS.hrdps.border }
  }

  const rdps: Plotly.Data = {
    x: [0.3, -1.3, 0.9, -0.2, 2.5, 1.6, -0.5, 1.0, 0.3, 1.5],
    type: 'box',
    name: 'RDPS',
    marker: { color: MORECAST_MODEL_COLORS.rdps.border }
  }

  const gdps: Plotly.Data = {
    x: [0.4, -1.5, 2.0, -0.5, 3.3, 1.6, -0.3, 0.9, 0.6, 1.7],
    type: 'box',
    name: 'GDPS',
    marker: { color: MORECAST_MODEL_COLORS.gdps.border }
  }

  const nam: Plotly.Data = {
    x: [-0.4, 1.3, -0.6, 0.1, -2.5, -0.8, 0.3, -0.7, -0.2, -1.6],
    type: 'box',
    name: 'NAM',
    marker: { color: MORECAST_MODEL_COLORS.nam.border }
  }

  const gfs: Plotly.Data = {
    x: [1.3, 1.9, 3.3, 4.1, 2.5, 0.8, -1.0, 1.6, 0.9, 2.3],
    type: 'box',
    name: 'GFS',
    marker: { color: MORECAST_MODEL_COLORS.gfs.border }
  }

  // const data = [hrdps, rdps, gdps, nam, gfs]
  const data: Plotly.Data[] = [hrdps, rdps, gdps, nam, gfs]

  const layout = {
    height: 300,
    title: {
      text: 'Temperature Difference (Predicted - Observed) °C'
    }
  }
  return <Plot data={data} layout={layout} />
}

export default SkillCharts2
