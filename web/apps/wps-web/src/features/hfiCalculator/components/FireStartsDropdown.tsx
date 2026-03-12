import { TextField, Autocomplete } from '@mui/material'
import { styled } from '@mui/material/styles'
import { FireStartRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { isEqual, isNull } from 'lodash'
import React from 'react'

const PREFIX = 'FireStartsDropdown'

const classes = {
  dropdownClass: `${PREFIX}-dropdownClass`
}

const StyledTextField = styled(TextField)({
  [`& .${classes.dropdownClass}`]: {
    width: '96px'
  }
})

export interface FireStartsDropdownProps {
  fireStarts: FireStartRange | undefined
  fireStartRanges: FireStartRange[]
  areaId: number
  dayOffset: number
  fireStartsEnabled: boolean
  setFireStarts: (areaId: number, dayOffset: number, newFireStarts: FireStartRange) => void
}

const FireStartsDropdown = ({
  fireStarts,
  fireStartRanges,
  areaId,
  dayOffset,
  fireStartsEnabled,
  setFireStarts
}: FireStartsDropdownProps) => {
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
      renderInput={params => <StyledTextField {...params} variant="outlined" />}
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
