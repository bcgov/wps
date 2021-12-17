import { TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import React from 'react'

export const FWIStationCell = () => {
  return (
    <Autocomplete
      autoHighlight={true}
      autoSelect={true}
      options={[]}
      renderInput={params => <TextField {...params} variant="outlined" size="small" />}
      // onChange={changeHandler}
      // disabled={props.disabled}
      value={null}
    />
  )
}
