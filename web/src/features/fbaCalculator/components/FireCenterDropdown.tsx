import { TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import { isEqual } from 'lodash'
import React, { useEffect, useState } from 'react'

interface FireCenterDropdownProps {
  value?: string
  fireCenterOptions: string[]
  disabled: boolean
}

const emptyLabel = 'Select a fire center'

const FireCenterDropdown = (props: FireCenterDropdownProps) => {
  const [selectedFireCenter, setSelectedFireCenter] = useState(props.value)
  useEffect(() => setSelectedFireCenter(props.value), [props])
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(selectedFireCenter, value)) {
      setSelectedFireCenter(value)
    }
  }

  return (
    <Autocomplete
      data-testid={`fire-center-dropdown`}
      options={props.fireCenterOptions}
      renderInput={params => (
        <TextField
          {...params}
          label={props.value ? '' : emptyLabel}
          variant="outlined"
          size="small"
        />
      )}
      onChange={changeHandler}
      disabled={props.disabled}
      value={selectedFireCenter}
    />
  )
}

export default React.memo(FireCenterDropdown)
