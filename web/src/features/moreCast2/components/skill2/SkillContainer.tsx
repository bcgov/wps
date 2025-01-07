import { ModelSkillEnum, ModelSkillSummaryData, RankedModelSkillSummaryData, WeatherParamEnum } from '@/api/skillAPI'
import { DateRange } from '@/components/dateRangePicker/types'
import SkillSelectionPanel2 from '@/features/moreCast2/components/skill2/SkillSelectionPanel2'
import SkillVisuals from '@/features/moreCast2/components/skill2/SkillVisuals'
import { SelectedModelByDate } from '@/features/moreCast2/interfaces'
import {
  selectedModelByDateChanged,
  selectSelectedModelByDate
} from '@/features/moreCast2/slices/selectedModelByDateSlice'
import { Box, Button, FormControl, InputLabel, MenuItem, Select, SelectChangeEvent, Typography } from '@mui/material'
import { isNil } from 'lodash'
import { DateTime } from 'luxon'
import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { AppDispatch } from 'app/store'
import { selectSkillData } from '@/features/moreCast2/slices/skillDataSlice'
import { selectSelectedStations } from '@/features/moreCast2/slices/selectedStationsSlice'

interface SkillContainerProps {
  fromTo: DateRange
}

const SkillContainer = ({ fromTo }: SkillContainerProps) => {
  const dispatch: AppDispatch = useDispatch()
  const [rankedModelSkillData, setRankedModelSkillData] = useState<RankedModelSkillSummaryData[]>([])
  const selectedModels = useSelector(selectSelectedModelByDate)
  const skillData = useSelector(selectSkillData)
  const selectedStations = useSelector(selectSelectedStations)
  const [selectedStationCodes, setSelectedStationCodes] = useState<number[]>([])
  const [forecastDatesInRange, setForecastDatesInRange] = useState<DateTime[]>([])
  const [selectedForecastIndex, setSelectedForecastIndex] = useState<string>('')
  const [weatherParameter, setWeatherParameter] = useState<WeatherParamEnum>(WeatherParamEnum.TEMP)

  const selectedModelSorter = (a: SelectedModelByDate, b: SelectedModelByDate) => {
    if (a.date < b.date) {
      return -1
    }
    if (a.date > b.date) {
      return 1
    }
    return 0
  }

  const getUTCTwentyToday = () => {
    const currentJSDate = new Date()
    const year = currentJSDate.getFullYear()
    const month = currentJSDate.getMonth() + 1 // month is zero indexed
    const day = currentJSDate.getDate()
    return DateTime.utc(year, month, day, 20)
  }

  const createForecastDateTimeArray = (fromTo: DateRange) => {
    if (isNil(fromTo.startDate) || isNil(fromTo.endDate)) {
      // No date range available, nothing to do
      return []
    }
    let startDateTime = DateTime.now()
    const endDateTime = DateTime.fromJSDate(fromTo.endDate).plus({ days: 1 })
    const dateTimeArray: DateTime[] = []
    // if (startDate.toJSDate() < fromTo.startDate || startDate.toJSDate() > fromTo.endDate) {
    //   return []
    // }

    if (startDateTime.toJSDate() > fromTo.endDate) {
      // All dates in range are in the past so no forecasting possible
      return []
    }

    const twentyHundredToday = getUTCTwentyToday()

    if (startDateTime.toUTC() > twentyHundredToday) {
      // Actuals should be available so first forecast date will be tomorrow, not today
      startDateTime = startDateTime.plus({ days: 1 })
    }
    while (startDateTime < endDateTime) {
      dateTimeArray.push(startDateTime)
      startDateTime = startDateTime.plus({ days: 1 })
    }
    return dateTimeArray
  }

  const updateSelectedModelByDate = (selected: ModelSkillEnum, date: DateTime) => {
    // If we have a model selected for this date replace it
    const selectedModelByDate = {
      adjustment: 0,
      date,
      model: selected,
      weatherParameter
    }
    const index = selectedModels.findIndex(selectedModel => {
      return selectedModel.date.startOf('day').toMillis() === date.startOf('day').toMillis()
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
    const daySkillData = weatherParamSkillData.daySkillData.find(
      daySkill => daySkill.day === parseInt(selectedForecastIndex)
    )
    if (isNil(daySkillData)) {
      return []
    }
    const modelSkillData: ModelSkillSummaryData[] = []
    for (const modelSkill of daySkillData.modelSkillData) {
      const filteredStationData = modelSkill.stationSkillData.filter(stationSkill =>
        selectedStationCodes.includes(stationSkill.stationCode)
      )
      const aggregateSkillData: number[] = []
      filteredStationData.forEach(station => aggregateSkillData.push(...station.skillData))
      if (aggregateSkillData.length === 0) {
        continue
      }
      const rmse = calculateRMSE(aggregateSkillData)
      modelSkillData.push({
        data: aggregateSkillData,
        model: modelSkill.model,
        rmse
      })
    }
    // const modelSkillData = daySkillData.modelSkillData.map(modelSkill => {
    //   const filteredStationData = modelSkill.stationSkillData.filter(stationSkill =>
    //     selectedStationCodes.includes(stationSkill.stationCode)
    //   )
    //   const aggregateSkillData: number[] = []
    //   filteredStationData.forEach(station => aggregateSkillData.push(...station.skillData))
    //   const rmse = calculateRMSE(aggregateSkillData)
    //   return {
    //     data: aggregateSkillData,
    //     model: modelSkill.model,
    //     rmse
    //   }
    // })
    return modelSkillData
  }

  const filterSkillDataByIndex = (index: number): ModelSkillSummaryData[] => {
    const weatherParamSkillData = skillData.find(x => x.weatherParam === weatherParameter)
    if (isNil(weatherParamSkillData)) {
      return []
    }
    const daySkillData = weatherParamSkillData.daySkillData.find(daySkill => daySkill.day === index)
    if (isNil(daySkillData)) {
      return []
    }
    const modelSkillData: ModelSkillSummaryData[] = []
    for (const modelSkill of daySkillData.modelSkillData) {
      const filteredStationData = modelSkill.stationSkillData.filter(stationSkill =>
        selectedStationCodes.includes(stationSkill.stationCode)
      )
      const aggregateSkillData: number[] = []
      filteredStationData.forEach(station => aggregateSkillData.push(...station.skillData))
      if (aggregateSkillData.length === 0) {
        continue
      }
      const rmse = calculateRMSE(aggregateSkillData)
      modelSkillData.push({
        data: aggregateSkillData,
        model: modelSkill.model,
        rmse
      })
    }
    return modelSkillData
  }

  const getRankedModelSkillData = (modelSkillData: ModelSkillSummaryData[]): RankedModelSkillSummaryData[] => {
    const orderedModelSkillData = [...modelSkillData]
    orderedModelSkillData.sort((a, b) => {
      return a.rmse - b.rmse
    })
    const rankedModelSkillData = orderedModelSkillData.map((data, index) => {
      return { ...data, rank: index + 1 }
    })
    return rankedModelSkillData
  }

  useEffect(() => {
    const newSelectedStationCodes = selectedStations.map(station => station.station_code)
    setSelectedStationCodes(newSelectedStationCodes)
  }, [selectedStations])

  useEffect(() => {
    const index = forecastDatesInRange.length > 0 ? '0' : ''
    setSelectedForecastIndex(index)
  }, [forecastDatesInRange])

  useEffect(() => {
    if (isNil(fromTo) || isNil(fromTo.startDate) || isNil(fromTo.endDate)) {
      return
    }
    const newDatesInRange = createForecastDateTimeArray(fromTo)
    setForecastDatesInRange(newDatesInRange)
  }, [fromTo])

  useEffect(() => {
    if (isNil(skillData)) {
      console.log('NILNilNIL')
      return
    }
    const skillDataForSelectedStations = filterSkillData()
    const newRankedModelSkillData = getRankedModelSkillData(skillDataForSelectedStations)
    setRankedModelSkillData(newRankedModelSkillData)
  }, [skillData, selectedStationCodes, selectedForecastIndex])

  const handleForecastDateChange = (param: SelectChangeEvent) => {
    const target = param?.target?.value
    setSelectedForecastIndex(target)
  }

  const handleWeatherParameterChange = (param: SelectChangeEvent) => {
    const target = (param?.target?.value as WeatherParamEnum) ?? WeatherParamEnum.TEMP
    setWeatherParameter(target)
  }

  const handleAutoSelectModels = () => {
    const newSelectedModels = []
    for (let i = 0; i < forecastDatesInRange.length; i++) {
      const filteredModelSkillData = filterSkillDataByIndex(i)
      const rankedSkillData = getRankedModelSkillData(filteredModelSkillData)
      newSelectedModels.push({
        adjustment: 0,
        date: forecastDatesInRange[i],
        model: rankedSkillData[0].model,
        weatherParameter
      })
    }
    newSelectedModels.sort(selectedModelSorter)
    dispatch(selectedModelByDateChanged(newSelectedModels))
  }

  const handleDeleteSelectedModel = (date: DateTime) => {
    const newSelectedModels = selectedModels.filter(model => model.date !== date)
    dispatch(selectedModelByDateChanged(newSelectedModels))
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ flexGrow: 1 }}>
        <Box sx={{ borderBottom: '1px solid #0e3367', padding: '12px' }}>
          <FormControl sx={{ width: '200px' }}>
            <InputLabel id="weather-parameter-selector-label">Weather Parameter</InputLabel>
            <Select
              labelId="weather-parameter-selector-label"
              id="weather-parameter-selector"
              value={weatherParameter}
              onChange={handleWeatherParameterChange}
              label="Weather Parameter"
              fullWidth
            >
              <MenuItem value={WeatherParamEnum.TEMP}>Temp</MenuItem>
              <MenuItem value={WeatherParamEnum.RH}>RH</MenuItem>
              <MenuItem value={WeatherParamEnum.WIND_DIR}>Wind Direction</MenuItem>
              <MenuItem value={WeatherParamEnum.WIND_SPEED}>Wind Speed</MenuItem>
              <MenuItem value={WeatherParamEnum.PRECIP}>Precip</MenuItem>
            </Select>
          </FormControl>
          <FormControl sx={{ marginLeft: '16px', width: '200px' }}>
            <InputLabel id="forecast-day-selector-label">Forecast Day</InputLabel>
            <Select
              labelId="forecast-day-selector-label"
              id="forecast-day-selector"
              value={selectedForecastIndex}
              onChange={handleForecastDateChange}
              label="Forecast Day"
            >
              {forecastDatesInRange.map((date: DateTime, index: number) => {
                return (
                  <MenuItem key={index} value={index}>
                    <Typography>{date.toLocaleString(DateTime.DATE_MED_WITH_WEEKDAY)}</Typography>
                  </MenuItem>
                )
              })}
            </Select>
          </FormControl>
          <Button onClick={handleAutoSelectModels} sx={{ margin: '8px 8px 8px 16px' }} variant="contained">
            {' '}
            Auto Select Models
          </Button>
        </Box>
        <SkillVisuals
          forecastDate={forecastDatesInRange[parseInt(selectedForecastIndex)]}
          rankedModelSkillData={rankedModelSkillData}
          weatherParameter={weatherParameter}
        />
        <SkillSelectionPanel2 deleteSelectedModel={handleDeleteSelectedModel} />
      </Box>
    </Box>
  )
}

export default SkillContainer
