import React, { useEffect, useState } from 'react'
import { styled } from '@mui/material/styles'
import { useDispatch, useSelector } from 'react-redux'
import { isEmpty } from 'lodash'
import { DateTime } from 'luxon'
import { selectAuthentication, selectStationGroups, selectStationGroupsMembers } from 'app/rootReducer'
import { AppDispatch } from 'app/store'
import { GeneralHeader } from 'components'
import { MORE_CAST_2_DOC_TITLE, MORE_CAST_2_NAME } from 'utils/constants'
import StationPanel from 'features/moreCast2/components/StationPanel'
import { DateRange } from 'components/dateRangePicker/types'
import { fetchStationGroups } from 'commonSlices/stationGroupsSlice'
import { StationGroup } from 'api/stationAPI'
import { fetchStationGroupsMembers } from 'commonSlices/selectedStationGroupMembers'
import { getWeatherIndeterminates, selectAllMoreCast2Rows } from 'features/moreCast2/slices/dataSlice'
import TabbedDataGrid from 'features/moreCast2/components/TabbedDataGrid'
import { selectedStationsChanged } from 'features/moreCast2/slices/selectedStationsSlice'
//test
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
  overflowX: 'auto'
}))

const MoreCast2Page = () => {
  const dispatch: AppDispatch = useDispatch()
  const { groups, loading: groupsLoading } = useSelector(selectStationGroups)
  const { members } = useSelector(selectStationGroupsMembers)
  const { idir } = useSelector(selectAuthentication)
  // All MoreCast2Rows derived from WeatherIndeterminates in dataSlice.ts. Updates in response to
  // a change of station group or date range.
  const sortedMoreCast2Rows = useSelector(selectAllMoreCast2Rows)
  const [selectedStationGroup, setSelectedStationGroup] = useState<StationGroup>()

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

  useEffect(() => {
    document.title = MORE_CAST_2_DOC_TITLE
    dispatch(fetchStationGroups())
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!isEmpty(members)) {
      dispatch(selectedStationsChanged([members[0]]))
      setSelectedGroupsMembers(members)
    }
    fetchWeatherIndeterminates()
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
  }, [fromTo.startDate, fromTo.endDate]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Root data-testid="more-cast-2-page">
      <GeneralHeader isBeta={true} spacing={0.985} title={MORE_CAST_2_NAME} productName={MORE_CAST_2_NAME} />
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
            morecast2Rows={sortedMoreCast2Rows}
            fetchWeatherIndeterminates={fetchWeatherIndeterminates}
            fromTo={fromTo}
            setFromTo={setFromTo}
          />
        </Observations>
      </Content>
    </Root>
  )
}

export default React.memo(MoreCast2Page)
