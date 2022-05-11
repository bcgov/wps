import { TextField, Autocomplete } from '@mui/material'
import { Option } from 'features/fwiCalculator/components/BasicFWIInput'
import { isEqual } from 'lodash'
import React from 'react'

export interface FWIStationCellProps {
  selectedStation: Option | null
  setSelectedStation: React.Dispatch<React.SetStateAction<Option | null>>
  isLoading: boolean
  stationOptions: Option[]
}
const emptyLabel = 'Select a station'

const FWIStationSelect = ({ isLoading, selectedStation, setSelectedStation, stationOptions }: FWIStationCellProps) => {
  return (
    <Autocomplete
      fullWidth
      autoHighlight={true}
      autoSelect={true}
      disabled={isLoading}
      options={stationOptions}
      getOptionLabel={option => `${option.name} (${option.code})`}
      isOptionEqualToValue={(option, value) => isEqual(option, value)}
      renderInput={params => (
        <TextField {...params} label={selectedStation ? '' : emptyLabel} variant="outlined" size="medium" fullWidth />
      )}
      onChange={(_, value) => {
        setSelectedStation(value)
      }}
      value={selectedStation}
    />
  )
}
export default React.memo(FWIStationSelect)
