import React, { useEffect, useState } from 'react'
import Plot from 'react-plotly.js'
import * as Plotly from 'plotly.js'
import { MORECAST_MODEL_COLORS } from 'app/theme'
import { Box } from '@mui/material'
import { RankedModelSkillStats } from '@/api/skillAPI'

interface SkillChartProps {
  rankedModelSkillStats: RankedModelSkillStats[]
}

const SkillChart = ({ rankedModelSkillStats }: SkillChartProps) => {
  const [plotlyData, setPlotlyData] = useState<Plotly.Data[]>([])
  useEffect(() => {
    const newRankedPlotlyData = rankedModelSkillStats.map(stats => {
      const modelLowercase = stats.model.toLowerCase()
      return {
        marker: { color: MORECAST_MODEL_COLORS[modelLowercase].border },
        name: stats.model as string,
        type: 'box',
        y: stats.raw
      } as Plotly.Data
    })
    setPlotlyData(newRankedPlotlyData)
  }, [rankedModelSkillStats])

  const layout = {
    title: {
      text: 'Temperature Difference (Predicted - Observed) °C'
    },
    height: 300,
    width: 450
  }
  return (
    <Box sx={{ display: 'flex', flexGrow: 1 }}>
      <Plot data={plotlyData} layout={layout} />
    </Box>
  )
}

export default SkillChart

// const hrdps: Plotly.Data = {
//   y: [0.2, -0.9, 0.6, -0.1, 2.5, 0.8, -0.3, 0.7, 0.2, 1.0],
//   type: 'box',
//   name: 'HRDPS',
//   marker: { color: MORECAST_MODEL_COLORS.hrdps.border }
// }

// const rdps: Plotly.Data = {
//   y: [0.3, -1.3, 0.9, -0.2, 2.5, 1.6, -0.5, 1.0, 0.3, 1.5],
//   type: 'box',
//   name: 'RDPS',
//   marker: { color: MORECAST_MODEL_COLORS.rdps.border }
// }

// const gdps: Plotly.Data = {
//   y: [0.4, -1.5, 2.0, -0.5, 3.3, 1.6, -0.3, 0.9, 0.6, 1.7],
//   type: 'box',
//   name: 'GDPS',
//   marker: { color: MORECAST_MODEL_COLORS.gdps.border }
// }

// const nam: Plotly.Data = {
//   y: [-0.4, 1.3, -0.6, 0.1, -2.5, -0.8, 0.3, -0.7, -0.2, -1.6],
//   type: 'box',
//   name: 'NAM',
//   marker: { color: MORECAST_MODEL_COLORS.nam.border }
// }

// const gfs: Plotly.Data = {
//   y: [1.3, 1.9, 3.3, 4.1, 2.5, 0.8, -1.0, 1.6, 0.9, 2.3],
//   type: 'box',
//   name: 'GFS',
//   marker: { color: MORECAST_MODEL_COLORS.gfs.border }
// }

// // const data = [hrdps, rdps, gdps, nam, gfs]
// const data: Plotly.Data[] = [hrdps, rdps, gdps, nam, gfs]
