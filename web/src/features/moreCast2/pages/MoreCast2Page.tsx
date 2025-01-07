import React, { useEffect, useState } from 'react'
import { styled } from '@mui/material/styles'
import { useDispatch, useSelector } from 'react-redux'
import { isEmpty, isNil } from 'lodash'
import { DateTime } from 'luxon'
import { selectAuthentication, selectStationGroups, selectStationGroupsMembers } from 'app/rootReducer'
import { AppDispatch } from 'app/store'
import { Button, GeneralHeader } from 'components'
import { MORE_CAST_DOC_TITLE, MORE_CAST_NAME } from 'utils/constants'
import StationPanel from 'features/moreCast2/components/StationPanel'
import { DateRange } from 'components/dateRangePicker/types'
import { fetchStationGroups } from 'commonSlices/stationGroupsSlice'
import { StationGroup } from 'api/stationAPI'
import { fetchStationGroupsMembers } from 'commonSlices/selectedStationGroupMembers'
import { getWeatherIndeterminates } from 'features/moreCast2/slices/dataSlice'
import TabbedDataGrid from 'features/moreCast2/components/TabbedDataGrid'
import { selectedStationsChanged, selectSelectedStations } from 'features/moreCast2/slices/selectedStationsSlice'
import { Box, Tab, Tabs } from '@mui/material'
import MorecastMapPanel from '@/features/moreCast2/components/map/MorecastMapPanel'
import { fetchSkillStats, SkillStatsResponse, WeatherParamSkillStats } from '@/api/skillAPI'
import { getSkillStats, selectSkillStats } from '@/features/moreCast2/slices/skillStatsSlice'
import SkillContainer from '@/features/moreCast2/components/skill2/SkillContainer'
import { getSkillData } from '@/features/moreCast2/slices/skillDataSlice'

export const Root = styled('div')({
  display: 'flex',
  flexDirection: 'column',
  minHeight: '100vh',
  overflow: 'hidden'
})

export const SidePanel = styled('div')({
  borderRight: '1px solid black',
  display: 'flex',
  minWidth: '375px',
  overflowX: 'hidden',
  overflowY: 'auto',
  width: '375px'
})

export const Content = styled('div')({
  borderTop: '1px solid black',
  display: 'flex',
  flexGrow: 1,
  maxHeight: 'calc(100vh - 71.5px)',
  overflow: 'hidden'
})

export const Observations = styled('div')(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  flexGrow: 1,
  marginTop: theme.spacing(2),
  overflow: 'hidden'
}))

enum TabView {
  TABLE = 0,
  MAP = 1,
  SKILL = 2
}

const MoreCast2Page = () => {
  const dispatch: AppDispatch = useDispatch()
  const { groups, loading: groupsLoading } = useSelector(selectStationGroups)
  const { members } = useSelector(selectStationGroupsMembers)
  const { idir } = useSelector(selectAuthentication)
  const [selectedStationGroup, setSelectedStationGroup] = useState<StationGroup>()
  const [tabValue, setTabValue] = useState<TabView>(TabView.TABLE)
  const selectedStations = useSelector(selectSelectedStations)
  const skillStats = useSelector(selectSkillStats)

  const currentTimeIsBeforeNoon = DateTime.now().hour < 13 ? true : false
  let startDateTime
  if (currentTimeIsBeforeNoon) {
    startDateTime = DateTime.now().minus({ days: 3 })
  } else {
    startDateTime = DateTime.now().minus({ days: 2 })
  }
  const endDateTime = startDateTime.plus({ days: 4 })
  const [fromTo, setFromTo] = useState<DateRange>({
    startDate: startDateTime.toJSDate(),
    endDate: endDateTime.toJSDate()
  })
  const [selectedGroupsMembers, setSelectedGroupsMembers] = useState([...members])

  const fetchWeatherIndeterminates = () => {
    if (fromTo?.startDate && fromTo?.endDate) {
      dispatch(
        getWeatherIndeterminates(members, DateTime.fromJSDate(fromTo.startDate), DateTime.fromJSDate(fromTo.endDate))
      )
    }
  }

  const fetchSkillData = () => {
    if (fromTo?.startDate && fromTo?.endDate) {
      const startDate = DateTime.fromObject({ year: 2024, month: 10, day: 15 })
      const stationCodes = members.map(member => member.station_code)
      dispatch(getSkillData(startDate, 7, stationCodes))
    }
  }

  useEffect(() => {
    document.title = MORE_CAST_DOC_TITLE
    dispatch(fetchStationGroups())
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isEmpty(members)) {
      dispatch(selectedStationsChanged([members[0]]))
      setSelectedGroupsMembers(members)
    }
    fetchWeatherIndeterminates()
    fetchSkillData()
  }, [members]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isEmpty(selectedStationGroup)) {
      dispatch(fetchStationGroupsMembers([selectedStationGroup.id]))
    } else {
      setSelectedGroupsMembers([])
    }
  }, [selectedStationGroup]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetchWeatherIndeterminates()
    fetchSkillData()
  }, [fromTo.startDate, fromTo.endDate]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleTabValueChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const handleFetchSkillStats = async () => {
    // if (isNil(fromTo) || isNil(fromTo?.startDate) || isNil(fromTo?.endDate) || selectedStations.length === 0) {
    //   return {
    //     skillStats: []
    //   }
    // }
    const twentyHundredUTCToday = DateTime.now().toUTC().set({ hour: 20 })
    const nowUTC = DateTime.now()
    // let startDate = DateTime.now()

    // if (startDate.toJSDate() < fromTo.startDate || startDate.toJSDate() > fromTo.endDate) {
    //   return { skillStats: [] }
    // }

    // if (startDate.toUTC().hour > 20) {
    //   startDate = startDate.plus({ days: 1 })
    // }

    const startDate = DateTime.fromObject({ year: 2024, month: 10, day: 15 })

    const stationCodes = selectedStations.map(s => s.station_code)
    dispatch(getSkillStats(startDate, 7, stationCodes))
  }

  return (
    <Root data-testid="more-cast-2-page">
      <GeneralHeader isBeta={false} spacing={0.985} title={MORE_CAST_NAME} productName={MORE_CAST_NAME} />
      <Content>
        <SidePanel>
          <StationPanel
            idir={idir}
            loading={groupsLoading}
            stationGroups={groups}
            selectedStationGroup={selectedStationGroup}
            setSelectedStationGroup={setSelectedStationGroup}
            stationGroupMembers={selectedGroupsMembers}
          />
        </SidePanel>
        <Box sx={{ display: 'flex', flexGrow: 1, flexDirection: 'column' }}>
          <Box sx={{ display: 'flex', flexDirection: 'row' }}>
            <Tabs value={tabValue} onChange={handleTabValueChange} sx={{ flexGrow: 1 }}>
              <Tab aria-label="Table" label="Table" />
              <Tab aria-label="Map" label="Map" />
              <Tab aria-label="Skill" label="Skill" />
            </Tabs>
            {tabValue === TabView.MAP && (
              <Button onClick={handleFetchSkillStats} sx={{ margin: '8px' }} variant="contained">
                Fetch
              </Button>
            )}
          </Box>
          {tabValue === TabView.TABLE && (
            <Observations>
              <TabbedDataGrid
                fromTo={fromTo}
                setFromTo={setFromTo}
                fetchWeatherIndeterminates={fetchWeatherIndeterminates}
              />
            </Observations>
          )}
          {tabValue === TabView.MAP && <MorecastMapPanel fromTo={fromTo} />}
          {tabValue === TabView.SKILL && <SkillContainer fromTo={fromTo} />}
        </Box>
      </Content>
    </Root>
  )
}

export default React.memo(MoreCast2Page)
