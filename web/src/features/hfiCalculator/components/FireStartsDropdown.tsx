import { TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import { isNull } from 'lodash'
import React from 'react'

const fireStartsOptions: string[] = ['0-1', '1-2', '2-3', '3-6', '6+']

export interface FireStartsDropdownProps {
  setFireStarts: (fireStarts: string) => void
}

const FireStartsDropdown = ({
  setFireStarts: setNumPrepDays
}: FireStartsDropdownProps) => {
  return (
    <Autocomplete
      data-testid={`fire-starts-dropdown`}
      disableClearable
      autoHighlight
      autoSelect
      options={fireStartsOptions}
      renderInput={params => <TextField {...params} variant="outlined" />}
      value={fireStartsOptions[0]}
      onChange={(_, value) => {
        if (!isNull(value)) {
          setNumPrepDays(value)
        }
      }}
    />
  )
}

export default React.memo(FireStartsDropdown)
