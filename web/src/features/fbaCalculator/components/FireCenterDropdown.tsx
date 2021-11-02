import { TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import { FireCenter } from 'api/fbaAPI'
import { isEqual } from 'lodash'
import React, { useEffect } from 'react'

interface FireCenterDropdownProps {
  selectedFireCenter?: FireCenter
  fireCenterOptions: FireCenter[]
  setSelectedFireCenter: React.Dispatch<React.SetStateAction<FireCenter | undefined>>
}

const FireCenterDropdown = (props: FireCenterDropdownProps) => {
  useEffect(() => {
    if (
      props.selectedFireCenter?.id.toString() !==
        localStorage.getItem('preferredFireCenter') &&
      props.selectedFireCenter?.id !== undefined
    ) {
      localStorage.setItem('preferredFireCenter', props.selectedFireCenter?.id.toString())
    }
  }, [props.selectedFireCenter])

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
      getOptionLabel={option => option?.name}
      renderInput={params => (
        <TextField {...params} label="Select Fire Center" variant="outlined" />
      )}
      onChange={changeHandler}
      value={props.selectedFireCenter}
    />
  )
}

export default React.memo(FireCenterDropdown)
