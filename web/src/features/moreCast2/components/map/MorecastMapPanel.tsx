import { ModelSkillStats, WeatherParamEnum, WeatherParamSkillStats } from '@/api/skillAPI'
import { DateRange } from '@/components/dateRangePicker/types'
import MorecastMap from '@/features/moreCast2/components/map/MorecastMap'
import SkillPanel2 from '@/features/moreCast2/components/skill/Skillpanel2'
import { Box, FormControl, InputLabel, MenuItem, Select, SelectChangeEvent, Typography } from '@mui/material'
import { isNil } from 'lodash'
import { DateTime } from 'luxon'
import { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import { selectSkillStats } from '@/features/moreCast2/slices/skillStatsSlice'

export enum WeatherParameter {
  TEMP = 'Temp',
  RH = 'RH'
}

interface MorecastMapPanelProps {
  fromTo: DateRange
}

const MorecastMapPanel = ({ fromTo }: MorecastMapPanelProps) => {
  const [weatherParameter, setWeatherParameter] = useState<WeatherParamEnum>(WeatherParamEnum.TEMP)
  const [forecastDatesInRange, setForecastDatesInRange] = useState<DateTime[]>([])
  const [selectedForecastIndex, setSelectedForecastIndex] = useState<string>('')
  const [selectedModelSkillStats, setSelectedModelSkillStats] = useState<ModelSkillStats[]>([])
  const skillStats = useSelector(selectSkillStats)

  const addDays = (date: Date, days: number) => {
    const newDate = new Date(date)
    newDate.setDate(date.getDate() + days)
    return newDate
  }

  const createDateTimeArray = (fromTo: DateRange): string[] => {
    if (isNil(fromTo.startDate) || isNil(fromTo.endDate)) {
      // No date range available, nothing to do
      return []
    }
    let startDateTime = DateTime.now()
    const endDateTime = DateTime.fromJSDate(fromTo.endDate).plus({ days: 1 })
    const dateTimeArray: string[] = []
    if (startDateTime.toJSDate() > fromTo.endDate) {
      // All dates in range are in the past so nothing to do
      return dateTimeArray
    }
    if (startDateTime.toUTC().hour > 20) {
      // Actuals should be available for today so first forecast date will be tomorrow, not today
      startDateTime = startDateTime.plus({ days: 1 })
    }
    while (startDateTime < endDateTime) {
      dateTimeArray.push(startDateTime.toLocaleString(DateTime.DATE_MED_WITH_WEEKDAY))
      startDateTime = startDateTime.plus({ days: 1 })
    }
    console.log(dateTimeArray)
    return dateTimeArray
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

  const handleWeatherParameterChange = (param: SelectChangeEvent) => {
    const target = (param?.target?.value as WeatherParamEnum) ?? WeatherParamEnum.TEMP
    setWeatherParameter(target)
  }

  const handleForecastDateChange = (param: SelectChangeEvent) => {
    const target = param?.target?.value
    setSelectedForecastIndex(target)
  }

  useEffect(() => {
    if (isNil(fromTo) || isNil(fromTo.startDate) || isNil(fromTo.endDate)) {
      return
    }
    const newDatesInRange = createForecastDateTimeArray(fromTo)
    setForecastDatesInRange(newDatesInRange)
  }, [fromTo])

  useEffect(() => {
    const index = forecastDatesInRange.length > 0 ? '0' : ''
    setSelectedForecastIndex(index)
  }, [forecastDatesInRange])

  useEffect(() => {
    const weatherParamSkillStats = skillStats.find(skill => skill.weatherParam === weatherParameter)
    const daySkillStats = weatherParamSkillStats?.daySkillStats.find(
      daySkill => daySkill.day === parseInt(selectedForecastIndex)
    )
    setSelectedModelSkillStats(daySkillStats?.modelSkillStats ?? [])
  }, [selectedForecastIndex, skillStats])

  return (
    <Box sx={{ display: 'flex', flexGrow: 1 }}>
      <MorecastMap selectedModelSkillStats={selectedModelSkillStats} />
      <Box
        sx={{ borderLeft: '1px solid #0e3367', borderTop: '1px solid #0e3367', minWidth: '450px', maxWidth: '450px' }}
      >
        <Box sx={{ padding: '8px' }}>
          <FormControl sx={{ width: '100%' }}>
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
        </Box>
        <Box sx={{ padding: '8px', width: '100%' }}>
          <FormControl sx={{ width: '100%' }}>
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
        </Box>
        <Box>
          {/* <SkillPanel /> */}
          <SkillPanel2
            forecastDate={forecastDatesInRange[parseInt(selectedForecastIndex)] ?? undefined}
            modelSkillStats={selectedModelSkillStats}
          />
        </Box>
      </Box>
    </Box>
  )
}

export default MorecastMapPanel
