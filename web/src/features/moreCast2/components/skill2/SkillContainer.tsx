import { ModelSkillEnum, RankedModelSkillSummaryData, WeatherParamEnum } from '@/api/skillAPI'
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

interface SkillContainerProps {
  fromTo: DateRange
}

const SkillContainer = ({ fromTo }: SkillContainerProps) => {
  const dispatch: AppDispatch = useDispatch()
  const [rankedModelSkillData, setRankedModelSkillData] = useState<RankedModelSkillSummaryData[]>([])
  const [forecastDatesInRange, setForecastDatesInRange] = useState<DateTime[]>([])
  const [selectedForecastIndex, setSelectedForecastIndex] = useState<string>('')
  const [weatherParameter, setWeatherParameter] = useState<WeatherParamEnum>(WeatherParamEnum.TEMP)
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

  const addSelectedModelByDate = (selected: ModelSkillEnum) => {
    const forecastDate = forecastDatesInRange[parseInt(selectedForecastIndex)]
    const selectedModelByDate = {
      adjustment: 0,
      date: forecastDate,
      model: selected,
      weatherParameter
    }
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

  const handleForecastDateChange = (param: SelectChangeEvent) => {
    const target = param?.target?.value
    setSelectedForecastIndex(target)
  }

  const handleWeatherParameterChange = (param: SelectChangeEvent) => {
    const target = (param?.target?.value as WeatherParamEnum) ?? WeatherParamEnum.TEMP
    setWeatherParameter(target)
  }

  const handleAutoSelectModels = () => {}

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
          <Button onClick={handleAutoSelectModels} variant="contained">
            {' '}
            Auto Select Models
          </Button>
        </Box>
        <SkillVisuals
          forecastDate={forecastDatesInRange[parseInt(selectedForecastIndex)]}
          selectedForecastIndex={parseInt(selectedForecastIndex)}
          weatherParameter={weatherParameter}
        />
        <SkillSelectionPanel2 deleteSelectedModel={handleDeleteSelectedModel} />
      </Box>
    </Box>
  )
}

export default SkillContainer
