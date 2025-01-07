import React, { useEffect, useState } from 'react'
import Plot from 'react-plotly.js'
import * as Plotly from 'plotly.js'
import { MORECAST_MODEL_COLORS } from 'app/theme'
import { Box, Button, Grid, Tab, Tabs, Typography } from '@mui/material'
import { AppDispatch } from 'app/store'
import SkillChart from '@/features/moreCast2/components/skill/SkillChart'
import SkillStats from '@/features/moreCast2/components/skill/SkillStats'
import SkillSelectionPanel from '@/features/moreCast2/components/skill/SkillSelectionPanel'
import { DateTime } from 'luxon'
import {
  ModelSkillEnum,
  ModelSkillStats,
  RankedModelSkillStats,
  WeatherParamEnum,
  WeatherParamSkillStats
} from '@/api/skillAPI'
import { WeatherParameter } from '@/features/moreCast2/components/map/MorecastMapPanel'
import { isNil } from 'lodash'
import { SelectedModelByDate } from '@/features/moreCast2/interfaces'
import { useDispatch, useSelector } from 'react-redux'
import {
  selectedModelByDateChanged,
  selectSelectedModelByDate
} from '@/features/moreCast2/slices/selectedModelByDateSlice'

enum SkillTabs {
  STATS = 0,
  CHART = 1
}

const selectedModelSorter = (a: SelectedModelByDate, b: SelectedModelByDate) => {
  if (a.date < b.date) {
    return -1
  }
  if (a.date > b.date) {
    return 1
  }
  return 0
}

interface SkillPanel2Props {
  forecastDate: DateTime
  modelSkillStats: ModelSkillStats[]
}

const SkillPanel2 = ({ forecastDate, modelSkillStats }: SkillPanel2Props) => {
  const dispatch: AppDispatch = useDispatch()
  const [skillTabValue, setSkillTabValue] = useState<SkillTabs>(SkillTabs.STATS)
  const [rankedModelSkillStats, setRankedModelSkillStats] = useState<RankedModelSkillStats[]>([])
  const selectedModels = useSelector(selectSelectedModelByDate)

  useEffect(() => {
    if (isNil(modelSkillStats)) {
      console.log('NILNilNIL')
      return
    }

    const orderedModelSkillStats = [...modelSkillStats]
    orderedModelSkillStats.sort((a, b) => {
      return a.rmse - b.rmse
    })
    const newRankedModelSkillStats = orderedModelSkillStats.map((stats, index) => {
      return { ...stats, rank: index + 1 }
    })
    setRankedModelSkillStats(newRankedModelSkillStats)
  }, [modelSkillStats])
  const handleSkillTabValueChange = (event: React.SyntheticEvent, newValue: number) => {
    setSkillTabValue(newValue)
  }
  const addSelectedModelByDate = (selected: ModelSkillEnum) => {
    const selectedModelByDate = { date: forecastDate, model: selected }
    // If we have a model selected for this date replace it
    const index = selectedModels.findIndex(selectedModel => {
      return selectedModel.date.startOf('day').toMillis() === forecastDate.startOf('day').toMillis()
    })
    let newSelectedModels: SelectedModelByDate[]
    if (index === -1) {
      newSelectedModels = [...selectedModels, selectedModelByDate]
    } else {
      newSelectedModels = [...selectedModels]
      newSelectedModels[index] = selectedModelByDate
    }
    newSelectedModels = newSelectedModels.sort(selectedModelSorter)
    dispatch(selectedModelByDateChanged(newSelectedModels))
  }
  const handleDeleteSelectedModel = (date: DateTime) => {
    const newSelectedModels = selectedModels.filter(model => model.date !== date)
    dispatch(selectedModelByDateChanged(newSelectedModels))
  }
  return (
    <Box>
      <Tabs value={skillTabValue} onChange={handleSkillTabValueChange}>
        <Tab aria-label="Stats" label="Stats" />
        <Tab aria-label="Chart" label="Chart" />
      </Tabs>
      {skillTabValue === SkillTabs.STATS && (
        <SkillStats addSelectedModel={addSelectedModelByDate} rankedModelSkillStats={rankedModelSkillStats} />
      )}
      {skillTabValue === SkillTabs.CHART && <SkillChart rankedModelSkillStats={rankedModelSkillStats} />}
      <SkillSelectionPanel deleteSelectedModel={handleDeleteSelectedModel} selectedModels={selectedModels} />
    </Box>
  )
}

export default SkillPanel2
