import React, { useEffect, useState } from 'react'
import Plot from 'react-plotly.js'
import * as Plotly from 'plotly.js'
import { MORECAST_MODEL_COLORS } from 'app/theme'
import { Box } from '@mui/material'
import { RankedModelSkillSummaryData } from '@/api/skillAPI'

interface SkillChart2Props {
  rankedModelSkillSummaryData: RankedModelSkillSummaryData[]
}

const SkillChart2 = ({ rankedModelSkillSummaryData }: SkillChart2Props) => {
  const [plotlyData, setPlotlyData] = useState<Plotly.Data[]>([])
  useEffect(() => {
    const newRankedPlotlyData = rankedModelSkillSummaryData.map(data => {
      const modelLowercase = data.model.toLowerCase()
      return {
        marker: { color: MORECAST_MODEL_COLORS[modelLowercase].border },
        name: data.model as string,
        type: 'box',
        y: data.data
      } as Plotly.Data
    })
    setPlotlyData(newRankedPlotlyData)
  }, [rankedModelSkillSummaryData])

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

export default SkillChart2
