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
import { Box } from '@mui/material'
import { DateTime } from 'luxon'
import { useDispatch, useSelector } from 'react-redux'

interface SkillVisualsProps {
  forecastDate: DateTime
  rankedModelSkillData: RankedModelSkillSummaryData[]
  weatherParameter: WeatherParamEnum
}

const SkillVisuals = ({ forecastDate, rankedModelSkillData, weatherParameter }: SkillVisualsProps) => {
  const dispatch: AppDispatch = useDispatch()
  const selectedModels = useSelector(selectSelectedModelByDate)
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
