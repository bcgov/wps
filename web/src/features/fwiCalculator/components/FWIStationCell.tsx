import { TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import { FWIInputParameters } from 'features/fwiCalculator/components/BasicFWIGrid'
import { Option } from 'features/fwiCalculator/components/BasicFWIInput'
import { isEqual } from 'lodash'
import React, { ChangeEvent } from 'react'

export interface FWIStationCellProps {
  stationOptions: Option[]
  input: FWIInputParameters
  setInput: React.Dispatch<React.SetStateAction<FWIInputParameters>>
}
const emptyLabel = 'Select a station'

const FWIStationCell = ({ stationOptions, input, setInput }: FWIStationCellProps) => {
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
    <React.Fragment>
      <Autocomplete
        autoHighlight={true}
        autoSelect={true}
        options={stationOptions}
        getOptionLabel={option => `${option.name} (${option.code})`}
        getOptionSelected={(option, value) => isEqual(option, value)}
        renderInput={params => (
          <TextField
            {...params}
            label={input.stationOption ? '' : emptyLabel}
            variant="outlined"
            size="small"
          />
        )}
        onChange={handleChange}
        value={input.stationOption}
      />
    </React.Fragment>
  )
}
export default React.memo(FWIStationCell)
