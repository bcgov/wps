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
  areaId: number
  dayOffset: number
  setFireStarts: (areaId: number, dayOffset: number, newFireStarts: FireStarts) => void
}

const FireStartsDropdown = ({
  fireStarts,
  areaId,
  dayOffset,
  setFireStarts
}: FireStartsDropdownProps) => {
  console.log('FireStartsDropdown', fireStarts, areaId, dayOffset)
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
          setFireStarts(areaId, dayOffset, value)
        }
      }}
    />
  )
}

export default React.memo(FireStartsDropdown)
