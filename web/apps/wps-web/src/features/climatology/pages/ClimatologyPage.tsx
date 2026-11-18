import { Alert, Box } from '@mui/material'
import { getStations, StationSource } from '@wps/api/stationAPI'
import { GeneralHeader } from '@wps/ui/GeneralHeader'
import { CLIMATOLOGY_NAME } from '@wps/utils/constants'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { sortBy } from 'lodash'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { selectFireWeatherStations } from '@/app/rootReducer'
import type { AppDispatch } from '@/app/store'
import ClimatologyView from '@/features/climatology/components/ClimatologyView'
import StationPicker from '@/features/climatology/components/StationPicker'
import type { StationOption } from '@/features/climatology/stationGroups'
import Footer from '@/features/landingPage/components/Footer'

export { MAX_STATIONS } from '@/features/climatology/components/ClimatologyView'

const ClimatologyPage = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { stations: allStations, error: stationsError } = useSelector(selectFireWeatherStations)
  const [stations, setStations] = useState<StationOption[]>([])
  // The name of the group the stations were chosen as, if they were.
  const [groupLabel, setGroupLabel] = useState<string | null>(null)
  const [groupError, setGroupError] = useState<string | null>(null)

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, [dispatch])

  const stationOptions = useMemo<StationOption[]>(
    () =>
      sortBy(
        allStations.map(({ properties }) => ({ code: properties.code, name: properties.name })),
        'name'
      ),
    [allStations]
  )
  const onStationsChange = useCallback((chosen: StationOption[], label: string | null) => {
    setStations(chosen)
    setGroupLabel(label)
  }, [])
  const onGroupError = useCallback((message: string) => setGroupError(message), [])

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <GeneralHeader isBeta={true} spacing={1} title={CLIMATOLOGY_NAME} />
      <Box sx={{ flex: 1, padding: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <StationPicker
          stationOptions={stationOptions}
          stations={stations}
          onChange={onStationsChange}
          onError={onGroupError}
        />
        {stationsError && <Alert severity="error">The list of weather stations could not be loaded.</Alert>}
        {groupError && (
          <Alert severity="warning" onClose={() => setGroupError(null)}>
            {groupError}
          </Alert>
        )}
        <ClimatologyView
          stations={stations}
          groupLabel={groupLabel}
          emptyMessage="Choose weather stations, or a fire centre, fire zone or station group, to compare a year of daily observations with their history."
        />
      </Box>
      <Footer />
    </Box>
  )
}

export default ClimatologyPage
