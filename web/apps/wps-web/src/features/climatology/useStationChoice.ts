import { getStations, StationSource } from '@wps/api/stationAPI'
import { fetchWxStations } from 'features/stations/slices/stationsSlice'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { selectFireWeatherStations } from '@/app/rootReducer'
import type { AppDispatch } from '@/app/store'
import type { StationOption } from '@/features/climatology/stationGroups'

/** The weather stations, and those chosen on the map. The stations load once `enabled`. */
export const useStationChoice = (enabled: boolean) => {
  const dispatch = useDispatch<AppDispatch>()
  const { stations, error } = useSelector(selectFireWeatherStations)
  const [chosenCodes, setChosenCodes] = useState<number[]>([])
  // The name of the stations when they were chosen by drawing an area.
  const [label, setLabel] = useState<string | null>(null)
  const [requested, setRequested] = useState(false)

  useEffect(() => {
    if (enabled && !requested) {
      setRequested(true)
      dispatch(fetchWxStations(getStations, StationSource.wildfire_one))
    }
  }, [dispatch, enabled, requested])

  const chosen = useMemo<StationOption[]>(() => {
    const names = new Map(stations.map(({ properties }) => [properties.code, properties.name]))
    return chosenCodes.map(code => ({ code, name: names.get(code) ?? `${code}` }))
  }, [stations, chosenCodes])

  const onChoose = useCallback((codes: number[], areaLabel: string | null) => {
    setChosenCodes(codes)
    setLabel(areaLabel)
  }, [])

  return { stations, error, chosenCodes, chosen, label, onChoose }
}
