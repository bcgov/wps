import React from 'react'
import { TextField, Autocomplete } from '@mui/material'
import { isEqual } from 'lodash'
import { ForecastActionType } from 'api/moreCast2API'

interface ForecastActionDropdownProps {
  label?: string
  selectedForecastAction: ForecastActionType
  forecastActionOptions: ForecastActionType[]
  setForecastAction: React.Dispatch<React.SetStateAction<ForecastActionType>>
}

const ForecastActionDropdown = (props: ForecastActionDropdownProps) => {
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(props.selectedForecastAction, value)) {
      props.setForecastAction(value)
    }
  }

  return (
    <Autocomplete
      sx={{ minWidth: 280 }}
      data-testid={`forecast-action-dropdown`}
      disableClearable
      options={props.forecastActionOptions}
      renderInput={params => (
        <TextField {...params} label={props.label ? props.label : 'Select Forecast Action'} variant="outlined" />
      )}
      onChange={changeHandler}
      isOptionEqualToValue={(option, value) => isEqual(option, value)}
      value={props.selectedForecastAction || null}
    />
  )
}

export default React.memo(ForecastActionDropdown)
