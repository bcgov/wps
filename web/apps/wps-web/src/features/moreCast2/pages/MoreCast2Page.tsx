import { fetchStationGroupsMembers } from 'commonSlices/selectedStationGroupMembers'
import { fetchStationGroups } from 'commonSlices/stationGroupsSlice'
import { styled } from '@mui/material/styles'
import type { StationGroup } from '@wps/api/stationAPI'
import type { DateRange } from '@wps/ui/dateRangePicker/types'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { MORE_CAST_DOC_TITLE, MORE_CAST_NAME } from '@wps/utils/constants'
import { selectAuthentication, selectStationGroups, selectStationGroupsMembers } from 'app/rootReducer'
import type { AppDispatch } from 'app/store'
import StationPanel from 'features/moreCast2/components/StationPanel'
import TabbedDataGrid from 'features/moreCast2/components/TabbedDataGrid'
import { getWeatherIndeterminates } from 'features/moreCast2/slices/dataSlice'
import { selectedStationsChanged } from 'features/moreCast2/slices/selectedStationsSlice'
import { isEmpty } from 'lodash'
import { DateTime } from 'luxon'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

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

const MoreCast2Page = () => {
  const dispatch: AppDispatch = useDispatch()
  const { groups, loading: groupsLoading } = useSelector(selectStationGroups)
  const { members } = useSelector(selectStationGroupsMembers)
  const { idir } = useSelector(selectAuthentication)
  const [selectedStationGroup, setSelectedStationGroup] = useState<StationGroup>()

  const currentTimeIsBeforeNoon = DateTime.now().hour < 13
  let startDateTime: DateTime
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

  useEffect(() => {
    document.title = MORE_CAST_DOC_TITLE
    dispatch(fetchStationGroups())
  }, [])

  useEffect(() => {
    if (!isEmpty(members)) {
      dispatch(selectedStationsChanged([members[0]]))
      setSelectedGroupsMembers(members)
    }
    fetchWeatherIndeterminates()
  }, [members])

  useEffect(() => {
    if (!isEmpty(selectedStationGroup)) {
      dispatch(fetchStationGroupsMembers([selectedStationGroup.id]))
    } else {
      setSelectedGroupsMembers([])
    }
  }, [selectedStationGroup])

  useEffect(() => {
    fetchWeatherIndeterminates()
  }, [fromTo.startDate, fromTo.endDate])

  return (
    <Root data-testid="more-cast-2-page">
      <GeneralHeader isBeta={false} spacing={0.985} title={MORE_CAST_NAME} />
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
        <Observations>
          <TabbedDataGrid
            fromTo={fromTo}
            setFromTo={setFromTo}
            fetchWeatherIndeterminates={fetchWeatherIndeterminates}
          />
        </Observations>
      </Content>
    </Root>
  )
}

export default React.memo(MoreCast2Page)
