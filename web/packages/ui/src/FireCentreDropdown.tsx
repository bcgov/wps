import { TextField, Autocomplete } from '@mui/material'
import { FireShape } from '@wps/api/fbaAPI'
import type { FireCentre } from '@wps/types/fireCentre'
import { isEqual, isNull } from 'lodash'
import React from 'react'

interface FireCentreDropdownProps {
  selectedFireCentre?: FireCentre
  fireCentreOptions: FireCentre[]
  setSelectedFireCentre: React.Dispatch<React.SetStateAction<FireCentre | undefined>>
  setSelectedFireShape: React.Dispatch<React.SetStateAction<FireShape | undefined>>
  setZoomSource: React.Dispatch<React.SetStateAction<'fireCentre' | 'fireShape' | undefined>>
}

const FireCentreDropdown = (props: FireCentreDropdownProps) => {
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(props.selectedFireCentre, value)) {
      props.setSelectedFireShape(undefined)
      props.setSelectedFireCentre(value ?? undefined)
      props.setZoomSource('fireCentre')
    }
    if (isNull(value)) {
      localStorage.removeItem('preferredFireCentre')
    }
  }

  return (
    <Autocomplete
      data-testid={`fire-center-dropdown`}
      options={props.fireCentreOptions}
      getOptionLabel={option => option?.name}
      renderInput={params => <TextField {...params} label="Select Fire Centre" variant="outlined" />}
      onChange={changeHandler}
      value={props.selectedFireCentre || null}
    />
  )
}

export default React.memo(FireCentreDropdown)
