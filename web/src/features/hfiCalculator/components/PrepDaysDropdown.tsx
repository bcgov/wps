import { TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import { isNull } from 'lodash'
import React from 'react'

export const MIN_PREP_DAYS = 2
export const MAX_PREP_DAYS = 7

const prepDayNumberOptions: string[] = ['2', '3', '4', '5', '7']

export interface PrepDaySelectProps {
  days: number
  setNumPrepDays: (numDays: number) => void
}

const PrepDaysDropdown = ({ days, setNumPrepDays }: PrepDaySelectProps) => {
  return (
    <Autocomplete
      data-testid={`prep-days-dropdown`}
      autoHighlight={true}
      autoSelect={true}
      options={prepDayNumberOptions}
      renderInput={params => (
        <TextField {...params} label="# Prep Days" variant="outlined" />
      )}
      value={String(days)}
      onChange={(_, value) => {
        if (!isNull(value)) {
          setNumPrepDays(Number(value))
        }
      }}
    />
  )
}

export default React.memo(PrepDaysDropdown)
