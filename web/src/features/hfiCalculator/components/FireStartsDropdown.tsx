import { TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import {
  FireStarts,
  FIRE_STARTS_SET,
  lowestFireStarts
} from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { isEqual, isNull } from 'lodash'
import React from 'react'

export interface FireStartsDropdownProps {
  fireStarts: FireStarts | undefined
  areaName: string
  dayOffset: number
  setFireStarts: (areaName: string, dayOffSet: number, newFireStarts: FireStarts) => void
}

const FireStartsDropdown = ({
  fireStarts,
  areaName,
  dayOffset,
  setFireStarts
}: FireStartsDropdownProps) => {
  return (
    <Autocomplete
      data-testid={`fire-starts-dropdown`}
      disableClearable
      autoHighlight
      autoSelect
      options={FIRE_STARTS_SET}
      getOptionSelected={(option, value) => isEqual(option, value)}
      getOptionLabel={option => option?.label}
      renderInput={params => <TextField {...params} variant="outlined" />}
      value={fireStarts ? fireStarts : lowestFireStarts}
      onChange={(_, value) => {
        if (!isNull(value)) {
          setFireStarts(areaName, dayOffset, value)
        }
      }}
    />
  )
}

export default React.memo(FireStartsDropdown)
