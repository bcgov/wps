import { TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import { Option } from 'features/fwiCalculator/components/BasicFWIInput'
import { isEqual } from 'lodash'
import React, { useState } from 'react'

export interface FWIStationCellProps {
  isLoading: boolean
  stationOptions: Option[]
}
const emptyLabel = 'Select a station'

const FWIMultiStationSelect = ({ isLoading, stationOptions }: FWIStationCellProps) => {
  const [selectedStation, setSelectedStation] = useState<Option | null>(null)
  return (
    <Autocomplete
      fullWidth
      autoHighlight={true}
      autoSelect={true}
      disabled={isLoading}
      options={stationOptions}
      getOptionLabel={option => `${option.name} (${option.code})`}
      getOptionSelected={(option, value) => isEqual(option, value)}
      renderInput={params => (
        <TextField
          {...params}
          label={selectedStation ? '' : emptyLabel}
          variant="outlined"
          size="medium"
          fullWidth
        />
      )}
      onChange={(_, value) => {
        setSelectedStation(value)
      }}
      value={selectedStation}
    />
  )
}
export default React.memo(FWIMultiStationSelect)
