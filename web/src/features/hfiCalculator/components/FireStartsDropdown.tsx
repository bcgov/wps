import { TextField, Autocomplete } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { FireStartRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { isEqual, isNull } from 'lodash'
import React from 'react'

export interface FireStartsDropdownProps {
  fireStarts: FireStartRange | undefined
  fireStartRanges: FireStartRange[]
  areaId: number
  dayOffset: number
  fireStartsEnabled: boolean
  setFireStarts: (areaId: number, dayOffset: number, newFireStarts: FireStartRange) => void
}

const useStyles = makeStyles({
  dropdownClass: {
    width: '96px'
  }
})

const FireStartsDropdown = ({
  fireStarts,
  fireStartRanges,
  areaId,
  dayOffset,
  fireStartsEnabled,
  setFireStarts
}: FireStartsDropdownProps) => {
  const classes = useStyles()
  return (
    <Autocomplete
      data-testid={`fire-starts-dropdown`}
      className={classes.dropdownClass}
      disabled={!fireStartsEnabled}
      disableClearable
      autoHighlight
      autoSelect
      options={fireStartRanges}
      isOptionEqualToValue={(option, value) => isEqual(option, value)}
      getOptionLabel={option => option?.label}
      renderInput={params => <TextField {...params} variant="outlined" />}
      value={fireStarts ? fireStarts : fireStartRanges[0]}
      onChange={(_, value) => {
        if (!isNull(value)) {
          setFireStarts(areaId, dayOffset, value)
        }
      }}
    />
  )
}

export default React.memo(FireStartsDropdown)
