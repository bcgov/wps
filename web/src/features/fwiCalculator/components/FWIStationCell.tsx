import { TextField, Autocomplete } from '@mui/material'
import { FWIInputParameters } from 'features/fwiCalculator/components/BasicFWIGrid'
import { Option } from 'features/fwiCalculator/components/BasicFWIInput'
import { isEqual } from 'lodash'
import React, { ChangeEvent } from 'react'

export interface FWIStationCellProps {
  isLoading: boolean
  stationOptions: Option[]
  input: FWIInputParameters
  setInput: React.Dispatch<React.SetStateAction<FWIInputParameters>>
}
const emptyLabel = 'Select a station'

const FWIStationCell = ({ isLoading, stationOptions, input, setInput }: FWIStationCellProps) => {
  // eslint-disable-next-line

  const handleChange = (
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    _: ChangeEvent<any>,
    value: Option | null
  ) => {
    setInput(prevState => ({
      ...prevState,
      stationOption: value
    }))
  }

  return (
    <Autocomplete
      autoHighlight={true}
      autoSelect={true}
      disabled={isLoading}
      options={stationOptions}
      getOptionLabel={option => `${option.name} (${option.code})`}
      isOptionEqualToValue={(option, value) => isEqual(option, value)}
      renderInput={params => (
        <TextField {...params} label={input.stationOption ? '' : emptyLabel} variant="outlined" size="small" />
      )}
      onChange={handleChange}
      value={input.stationOption}
    />
  )
}
export default React.memo(FWIStationCell)
