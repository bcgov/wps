import { Alert, Box } from '@mui/material'
import { getStations, StationSource } from '@wps/api/stationAPI'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { selectFireWeatherStations } from '@/app/rootReducer'
import type { AppDispatch } from '@/app/store'
import ClimatologyView from '@/features/climatology/components/ClimatologyView'
import StationClimatologyMap from '@/features/climatology/components/map/StationClimatologyMap'
import type { StationOption } from '@/features/climatology/stationGroups'

/** A map of the stations beside the climatology of those chosen on it. */
const StationClimatologyPanel = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { stations, error } = useSelector(selectFireWeatherStations)
  const [chosenCodes, setChosenCodes] = useState<number[]>([])
  // The name of the stations when they were chosen by drawing an area.
  const [label, setLabel] = useState<string | null>(null)

  useEffect(() => {
    dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
  }, [dispatch])

  const chosen = useMemo<StationOption[]>(() => {
    const names = new Map(stations.map(({ properties }) => [properties.code, properties.name]))
    return chosenCodes.map(code => ({ code, name: names.get(code) ?? `${code}` }))
  }, [stations, chosenCodes])

  const onChoose = useCallback((codes: number[], areaLabel: string | null) => {
    setChosenCodes(codes)
    setLabel(areaLabel)
  }, [])

  return (
    <Box
      data-testid="station-climatology-panel"
      sx={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: { xs: 'column', md: 'row' } }}
    >
      <Box sx={{ position: 'relative', width: { xs: '100%', md: '42%' }, height: { xs: 360, md: 'auto' } }}>
        <StationClimatologyMap stations={stations} chosenCodes={chosenCodes} onChoose={onChoose} />
      </Box>
      <Box
        sx={{ flex: 1, minWidth: 0, overflowY: 'auto', padding: 2, display: 'flex', flexDirection: 'column', gap: 2 }}
      >
        {error && <Alert severity="error">The list of weather stations could not be loaded.</Alert>}
        <ClimatologyView
          stations={chosen}
          groupLabel={label}
          emptyMessage="Click a station on the map, or draw an area around several, to compare a year of daily observations with their history."
        />
      </Box>
    </Box>
  )
}

export default StationClimatologyPanel
