import { TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import { isEqual } from 'lodash'
import React from 'react'

interface FireCenterDropdownProps {
  selectedFireCenter?: string
  fireCenterOptions: string[]
  setSelectedFireCenter: React.Dispatch<React.SetStateAction<string | undefined>>
}

const FireCenterDropdown = (props: FireCenterDropdownProps) => {
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(props.selectedFireCenter, value)) {
      props.setSelectedFireCenter(value)
    }
  }

  return (
    <Autocomplete
      data-testid={`fire-center-dropdown`}
      options={props.fireCenterOptions}
      renderInput={params => (
        <TextField {...params} label="Select Fire Center" variant="outlined" />
      )}
      onChange={changeHandler}
      value={props.selectedFireCenter}
    />
  )
}

export default React.memo(FireCenterDropdown)
