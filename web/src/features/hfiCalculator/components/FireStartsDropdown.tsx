import { makeStyles, TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import { FireStartRange } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { isEqual, isNull } from 'lodash'
import React from 'react'

export interface FireStartsDropdownProps {
  fireStarts: FireStartRange | undefined
  fireStartRanges: FireStartRange[]
  areaId: number
  dayOffset: number
  setFireStarts: (
    areaId: number,
    dayOffset: number,
    newFireStarts: FireStartRange
  ) => void
}

const useStyles = makeStyles({
  thing: {
    width: '96px'
  }
})

const FireStartsDropdown = ({
  fireStarts,
  fireStartRanges,
  areaId,
  dayOffset,
  setFireStarts
}: FireStartsDropdownProps) => {
  const classes = useStyles()
  return (
    <Autocomplete
      data-testid={`fire-starts-dropdown`}
      className={classes.thing}
      disableClearable
      autoHighlight
      autoSelect
      options={fireStartRanges}
      getOptionSelected={(option, value) => isEqual(option, value)}
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
