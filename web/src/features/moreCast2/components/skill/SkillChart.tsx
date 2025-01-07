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

