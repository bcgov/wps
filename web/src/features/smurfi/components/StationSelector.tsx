import React, { useEffect, useState } from 'react'
import { useSelector } from 'react-redux'
import { Autocomplete, TextField } from '@mui/material'
import { GeoJsonStation } from '@/api/stationAPI'
import { selectFireWeatherStations } from '@/app/rootReducer'
import { Option as StationOption } from 'utils/dropdown'

interface StationSelectorProps {
  value: number[]
  onChange: (value: number[]) => void
}

const StationSelector: React.FC<StationSelectorProps> = ({ value, onChange }) => {
  const [stationOptions, setStationOptions] = useState<StationOption[]>([])
  const { stations } = useSelector(selectFireWeatherStations)

  useEffect(() => {
    const allStationOptions: StationOption[] = (stations as GeoJsonStation[]).map(station => ({
      name: `${station.properties.name} (${station.properties.code})`,
      code: station.properties.code
    }))
    setStationOptions(allStationOptions)
  }, [stations])

  return (
    <Autocomplete
      multiple
      options={stationOptions}
      getOptionLabel={option => option.name}
      value={stationOptions.filter(option => value.includes(option.code))}
      onChange={(_, newValue) => {
        onChange(newValue.map(v => v.code))
      }}
      renderInput={params => <TextField {...params} label="Weather Stations" />}
    />
  )
}

export default StationSelector
