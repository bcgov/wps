import {
  ModelSkillEnum,
  ModelSkillStats,
  RankedModelSkillStats,
  RankedModelSkillSummaryData,
  WeatherParamEnum,
  WeatherParamSkillStats
} from '@/api/skillAPI'
import { WeatherParameter } from '@/features/moreCast2/components/map/MorecastMapPanel'
import ModelSkillGridItem from '@/features/moreCast2/components/skill/ModelSkillGridItem'
import ModelSkillGridItem2 from '@/features/moreCast2/components/skill/ModelSkillGridItem2'
import { Box, Button, Grid, Typography } from '@mui/material'
import { isNil } from 'lodash'
import { DateTime } from 'luxon'
import { useEffect, useState } from 'react'

interface SkillStatsProps {
  addSelectedModel: (selectedModel: ModelSkillEnum) => void
  rankedModelSkillStats: RankedModelSkillStats[]
}

const SkillStats = ({ addSelectedModel, rankedModelSkillStats }: SkillStatsProps) => {
  return (
    <Box sx={{ padding: '32px', minHeight: '300px' }}>
      <Typography sx={{ fontWeight: 'bold', paddingBottom: '16px' }}>Mean Squared Error</Typography>
      <Grid container rowSpacing={8}>
        <Grid item xs={3}>
          <Typography fontWeight="bold">Model</Typography>
        </Grid>
        <Grid item xs={3}>
          <Typography fontWeight="bold">RMSE</Typography>
        </Grid>
        <Grid item xs={3}>
          <Typography fontWeight="bold">Rank</Typography>
        </Grid>
        <Grid item xs={3}>
          <Typography fontWeight="bold">Action</Typography>
        </Grid>
        {rankedModelSkillStats.map(stat => {
          return <ModelSkillGridItem addSelectedModel={addSelectedModel} key={stat.model} stats={stat} />
        })}
      </Grid>
    </Box>
  )
}

export default SkillStats
