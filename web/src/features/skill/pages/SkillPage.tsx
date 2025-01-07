import { useEffect } from 'react'
import { DateRange } from '@/components/dateRangePicker/types'
import { GeneralHeader } from '@/components/GeneralHeader'
import { useDispatch, useSelector } from 'react-redux'
import Footer from '@/features/landingPage/components/Footer'
import MoreCast2DateRangePicker from '@/features/moreCast2/components/MoreCast2DateRangePicker'
import SkillMap from '@/features/skill/components/SkillMap'
import SkillCharts from '@/features/skill/components/SkillCharts'
import { SKILL_NAME } from '@/utils/constants'
import { FormControl, InputLabel, MenuItem, Select, SelectChangeEvent } from '@mui/material'
import Box from '@mui/material/Box'
import { DateTime } from 'luxon'
import { useState } from 'react'
import StationGroupDropdown from '@/features/moreCast2/components/StationGroupDropdown'
import { selectAuthentication, selectStationGroups, selectStationGroupsMembers } from 'app/rootReducer'
import { StationGroup } from '@/api/stationAPI'
import { fetchStationGroups } from '@/commonSlices/stationGroupsSlice'
import { AppDispatch } from '@/app/store'

enum WeatherParameter {
  TEMP = 'Temp',
  RH = 'RH'
}

const startDateTime = DateTime.now()
const endDateTime = startDateTime.plus({ days: 4 })

const SkillPage = () => {
  const dispatch: AppDispatch = useDispatch()
  const [fromTo, setFromTo] = useState<DateRange>({
    startDate: startDateTime.toJSDate(),
    endDate: endDateTime.toJSDate()
  })
  const [weatherParameter, setWeatherParameter] = useState<WeatherParameter>(WeatherParameter.TEMP)
  const [forecastDay, setForecastDay] = useState<number>(1)
  const { idir } = useSelector(selectAuthentication)
  const { groups, loading: groupsLoading } = useSelector(selectStationGroups)
  const [selectedStationGroup, setSelectedStationGroup] = useState<StationGroup>()

  const handleWeatherParameterChange = (param: SelectChangeEvent) => {
    const target = (param?.target?.value as WeatherParameter) ?? WeatherParameter.TEMP
    setWeatherParameter(target)
  }
  const handleForecastDayChange = (param: SelectChangeEvent<number>) => {
    const target = parseInt(`${param?.target?.value}`) ?? 1
    setForecastDay(target)
  }

  useEffect(() => {
    dispatch(fetchStationGroups())
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <GeneralHeader isBeta={true} spacing={1} title={SKILL_NAME} productName={SKILL_NAME} />
      <Box sx={{ display: 'flex', flex: 1, flexDirection: 'row' }}>
        <Box
          sx={{
            borderRight: '1px solid #0e3367',
            display: 'flex',
            flexDirection: 'column',
            width: '400px',
            height: '100%'
          }}
        >
          <MoreCast2DateRangePicker dateRange={fromTo} setDateRange={setFromTo} />
          <Box sx={{ padding: '8px', width: '100%' }}>
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
                <MenuItem value={'Temp'}>Temp</MenuItem>
                <MenuItem value={'RH'}>RH</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Box sx={{ padding: '8px', width: '100%' }}>
            <FormControl sx={{ width: '100%' }}>
              <InputLabel id="forecast-day-selector-label">Forecast Day</InputLabel>
              <Select<number>
                labelId="forecast-day-selector-label"
                id="forecast-day-selector"
                value={forecastDay}
                onChange={handleForecastDayChange}
                label="Forecast Day"
              >
                <MenuItem value={1}>1</MenuItem>
                <MenuItem value={2}>2</MenuItem>
                <MenuItem value={3}>3</MenuItem>
                <MenuItem value={4}>4</MenuItem>
                <MenuItem value={5}>5</MenuItem>
              </Select>
            </FormControl>
          </Box>
          {/* <Box sx={{ padding: '8px', width: '100%' }}>
            <FormControl>
              <StationGroupDropdown
                idir={idir}
                stationGroupOptions={groups}
                selectedStationGroup={selectedStationGroup}
                setSelectedStationGroup={setSelectedStationGroup}
              />
            </FormControl>
          </Box> */}
        </Box>
        <Box sx={{ display: 'flex', flex: 1, flexDirection: 'column' }}>
          <SkillMap />
          <Box sx={{ height: '300px' }}>
            <SkillCharts />
          </Box>
        </Box>
      </Box>
      <Footer />
    </Box>
  )
}

export default SkillPage
