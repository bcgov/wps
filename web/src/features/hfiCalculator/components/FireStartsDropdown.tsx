import { TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import { FireStarts } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { isEqual, isNull } from 'lodash'
import React from 'react'

export interface FireStartsDropdownProps {
  fireStarts: FireStarts | undefined
  allFireStarts: FireStarts[]
  areaId: number
  dayOffset: number
  setFireStarts: (areaId: number, dayOffset: number, newFireStarts: FireStarts) => void
}

const FireStartsDropdown = ({
  fireStarts,
  allFireStarts,
  areaId,
  dayOffset,
  setFireStarts
}: FireStartsDropdownProps) => {
  const fireCentreFireStartsOptions = allFireStarts ? allFireStarts : []
  const initialOption =
    fireCentreFireStartsOptions.length > 0 ? fireCentreFireStartsOptions[0] : undefined
  return (
    <Autocomplete
      data-testid={`fire-starts-dropdown`}
      disableClearable
      autoHighlight
      autoSelect
      options={allFireStarts}
      getOptionSelected={(option, value) => isEqual(option, value)}
      getOptionLabel={option =>
        option.max_starts > 15
          ? `${option.min_starts}+`
          : `${option.min_starts}-${option.max_starts}`
      }
      renderInput={params => <TextField {...params} variant="outlined" />}
      value={fireStarts ? fireStarts : initialOption}
      onChange={(_, value) => {
        if (!isNull(value)) {
          setFireStarts(areaId, dayOffset, value)
        }
      }}
    />
  )
}

export default React.memo(FireStartsDropdown)
