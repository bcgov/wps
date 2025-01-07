import {
  DaySkillData,
  ModelSkillEnum,
  ModelSkillSummaryData,
  RankedModelSkillSummaryData,
  WeatherParamEnum
} from '@/api/skillAPI'
import { AppDispatch } from '@/app/store'
import SkillChart from '@/features/moreCast2/components/skill/SkillChart'
import SkillStats from '@/features/moreCast2/components/skill/SkillStats'
import SkillChart2 from '@/features/moreCast2/components/skill2/SkillChart2'
import SkillStats2 from '@/features/moreCast2/components/skill2/SkillStats2'
import { SelectedModelByDate } from '@/features/moreCast2/interfaces'
import {
  selectedModelByDateChanged,
  selectSelectedModelByDate
} from '@/features/moreCast2/slices/selectedModelByDateSlice'
import { selectSelectedStations } from '@/features/moreCast2/slices/selectedStationsSlice'
import { selectSkillData } from '@/features/moreCast2/slices/skillDataSlice'
import { Box } from '@mui/material'
import { isNil } from 'lodash'
import { DateTime } from 'luxon'
import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

interface SkillVisualsProps {
  forecastDate: DateTime
  selectedForecastIndex: number
  weatherParameter: WeatherParamEnum
}

const SkillVisuals = ({ forecastDate, selectedForecastIndex, weatherParameter }: SkillVisualsProps) => {
  const dispatch: AppDispatch = useDispatch()
  const [rankedModelSkillData, setRankedModelSkillData] = useState<RankedModelSkillSummaryData[]>([])
  const selectedModels = useSelector(selectSelectedModelByDate)
  const skillData = useSelector(selectSkillData)
  const selectedStations = useSelector(selectSelectedStations)
  const [selectedStationCodes, setSelectedStationCodes] = useState<number[]>([])
  const selectedModelSorter = (a: SelectedModelByDate, b: SelectedModelByDate) => {
    if (a.date < b.date) {
      return -1
    }
    if (a.date > b.date) {
      return 1
    }
    return 0
  }

  const addSelectedModelByDate = (selected: ModelSkillEnum) => {
    // If we have a model selected for this date replace it
    const selectedModelByDate = {
      adjustment: 0,
      date: forecastDate,
      model: selected,
      weatherParameter
    }
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

  const calculateRMSE = (data: number[]) => {
    let sum = 0
    data.forEach(d => (sum += d * d))
    return Math.sqrt(sum)
  }

  const filterSkillData = (): ModelSkillSummaryData[] => {
    const weatherParamSkillData = skillData.find(x => x.weatherParam === weatherParameter)
    if (isNil(weatherParamSkillData)) {
      return []
    }
    const daySkillData = weatherParamSkillData.daySkillData.find(daySkill => daySkill.day === selectedForecastIndex)
    if (isNil(daySkillData)) {
      return []
    }
    const modelSkillData = daySkillData.modelSkillData.map(modelSkill => {
      const filteredStationData = modelSkill.stationSkillData.filter(stationSkill =>
        selectedStationCodes.includes(stationSkill.stationCode)
      )
      const aggregateSkillData: number[] = []
      filteredStationData.forEach(station => aggregateSkillData.push(...station.skillData))
      const rmse = calculateRMSE(aggregateSkillData)
      return {
        data: aggregateSkillData,
        model: modelSkill.model,
        rmse
      }
    })
    return modelSkillData
  }

  useEffect(() => {
    const newSelectedStationCodes = selectedStations.map(station => station.station_code)
    setSelectedStationCodes(newSelectedStationCodes)
  }, [selectedStations])

  useEffect(() => {
    if (isNil(skillData)) {
      console.log('NILNilNIL')
      return
    }

    const skillDataForSelectedStations = filterSkillData()
    const orderedModelSkillStats = [...skillDataForSelectedStations]
    orderedModelSkillStats.sort((a, b) => {
      return a.rmse - b.rmse
    })
    const newRankedModelSkillStats = orderedModelSkillStats.map((stats, index) => {
      return { ...stats, rank: index + 1 }
    })
    setRankedModelSkillData(newRankedModelSkillStats)
  }, [skillData, selectedStationCodes, selectedForecastIndex])
  return (
    <Box sx={{ borderBottom: '1px solid #0e3367', display: 'flex', height: '325px' }}>
      <Box sx={{ maxWidth: '400px' }}>
        <SkillStats2 addSelectedModel={addSelectedModelByDate} rankedModelSkillStats={rankedModelSkillData} />
      </Box>
      <Box sx={{ flexGrow: 1 }}>
        <SkillChart2 rankedModelSkillSummaryData={rankedModelSkillData} />
      </Box>
    </Box>
  )
}

export default SkillVisuals
