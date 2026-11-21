import { fetchStationGroupsMembers } from 'commonSlices/selectedStationGroupMembers'
import { fetchStationGroups } from 'commonSlices/stationGroupsSlice'
import { Box } from '@mui/material'
import { styled } from '@mui/material/styles'
import type { StationGroup } from '@wps/api/stationAPI'
import type { DateRange } from '@wps/ui/dateRangePicker/types'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { MORE_CAST_DOC_TITLE, MORE_CAST_NAME } from '@wps/utils/constants'
import { type RootState, selectAuthentication, selectStationGroups, selectStationGroupsMembers } from 'app/rootReducer'
import type { AppDispatch } from 'app/store'
import ModelElevationComparisonPanel from 'features/moreCast2/components/ModelElevationComparisonPanel'
import StationPanel from 'features/moreCast2/components/StationPanel'
import TabbedDataGrid, { type ElevationAdjustmentHandle } from 'features/moreCast2/components/TabbedDataGrid'
import { getModelElevationData } from 'features/moreCast2/modelElevation'
import { getWeatherIndeterminates, selectAllMoreCast2Rows } from 'features/moreCast2/slices/dataSlice'
import { selectedStationsChanged, selectSelectedStations } from 'features/moreCast2/slices/selectedStationsSlice'
import { getDefaultDateRange } from 'features/moreCast2/util'
import { isEmpty } from 'lodash'
import { DateTime } from 'luxon'
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'

export const Root = styled('div')({
  display: 'flex',
  flexDirection: 'column',
  minHeight: '100vh',
  overflow: 'hidden'
})

export const SidePanel = styled('div')({
  position: 'relative',
  borderRight: '1px solid black',
  display: 'flex',
  flexDirection: 'column',
  minWidth: '375px',
  overflowX: 'hidden',
  overflowY: 'hidden',
  width: '375px'
})

export const Content = styled('div')({
  borderTop: '1px solid black',
  display: 'flex',
  flexGrow: 1,
  maxHeight: 'calc(100vh - 71.5px)',
  overflow: 'hidden'
})

export const Observations = styled('div')({
  display: 'flex',
  flexDirection: 'column',
  flexGrow: 1,
  overflow: 'hidden'
})

const MoreCast2Page = () => {
  // store
  const dispatch: AppDispatch = useDispatch()
  const { groups, loading: groupsLoading } = useSelector(selectStationGroups)
  const { members } = useSelector(selectStationGroupsMembers)
  const { idir } = useSelector(selectAuthentication)
  const selectedStations = useSelector(selectSelectedStations)
  const morecast2Rows = useSelector(selectAllMoreCast2Rows)
  const modelPredictions = useSelector((state: RootState) => state.weatherIndeterminates.predictions)

  const gridRef = useRef<ElevationAdjustmentHandle>(null)

  // state
  const [selectedStationGroup, setSelectedStationGroup] = useState<StationGroup>()

  const [fromTo, setFromTo] = useState<DateRange>(() => getDefaultDateRange())
  const [selectedGroupsMembers, setSelectedGroupsMembers] = useState([...members])
  const [comparisonStationCode, setComparisonStationCode] = useState<number | null>(null)

  // derived data
  const modelElevationData = useMemo(() => {
    const stationCodes = new Set(selectedStations.map(station => station.station_code))
    const modelRows = morecast2Rows.filter(row => stationCodes.has(row.stationCode))
    return getModelElevationData(modelRows, modelPredictions, selectedStations)
  }, [morecast2Rows, modelPredictions, selectedStations])
  const comparisonStation = selectedStations.find(station => station.station_code === comparisonStationCode)

  // callbacks
  const fetchWeatherIndeterminates = useCallback(() => {
    if (fromTo?.startDate && fromTo?.endDate) {
      dispatch(
        getWeatherIndeterminates(members, DateTime.fromJSDate(fromTo.startDate), DateTime.fromJSDate(fromTo.endDate))
      )
    }
  }, [dispatch, members, fromTo.startDate, fromTo.endDate])

  // effects
  useEffect(() => {
    if (!comparisonStation) setComparisonStationCode(null)
  }, [comparisonStation])

  useEffect(() => {
    document.title = MORE_CAST_DOC_TITLE
    dispatch(fetchStationGroups())
  }, [dispatch])

  useEffect(() => {
    if (!isEmpty(members)) {
      dispatch(selectedStationsChanged([members[0]]))
      setSelectedGroupsMembers(members)
    }
  }, [members, dispatch])

  useEffect(() => {
    if (isEmpty(selectedStationGroup)) {
      setSelectedGroupsMembers([])
    } else {
      dispatch(fetchStationGroupsMembers([selectedStationGroup.id]))
    }
  }, [selectedStationGroup, dispatch])

  useEffect(() => {
    fetchWeatherIndeterminates()
  }, [fetchWeatherIndeterminates])

  // render
  return (
    <Root data-testid="more-cast-2-page">
      <GeneralHeader isBeta={false} spacing={0.985} title={MORE_CAST_NAME} />
      <Content>
        <SidePanel>
          {/* keep the selector mounted so closing restores its selection and scroll position */}
          <Box sx={{ display: 'flex', flex: 1, minHeight: 0, visibility: comparisonStation ? 'hidden' : 'visible' }}>
            <StationPanel
              idir={idir}
              loading={groupsLoading}
              stationGroups={groups}
              selectedStationGroup={selectedStationGroup}
              setSelectedStationGroup={setSelectedStationGroup}
              stationGroupMembers={selectedGroupsMembers}
            />
          </Box>
          <ModelElevationComparisonPanel
            key={comparisonStationCode ?? 'closed'}
            onApply={(model, adjustmentCelsius, overwriteExisting) =>
              gridRef.current?.applyElevationAdjustment(
                comparisonStationCode!,
                model,
                adjustmentCelsius,
                overwriteExisting
              ) ?? 'Forecast data is unavailable.'
            }
            station={
              comparisonStation
                ? {
                    stationName: comparisonStation.display_label,
                    stationElevation: comparisonStation.elevation ?? null,
                    modelElevations:
                      modelElevationData.stationElevations.get(comparisonStation.station_code)?.modelElevations ?? {}
                  }
                : null
            }
            onClose={() => setComparisonStationCode(null)}
          />
        </SidePanel>
        <Observations>
          <TabbedDataGrid
            ref={gridRef}
            fromTo={fromTo}
            setFromTo={setFromTo}
            fetchWeatherIndeterminates={fetchWeatherIndeterminates}
            modelElevationData={modelElevationData}
            onCompareElevations={setComparisonStationCode}
          />
        </Observations>
      </Content>
    </Root>
  )
}

export default React.memo(MoreCast2Page)
