import React from 'react'
import { TextField, Autocomplete } from '@mui/material'
import { isEqual } from 'lodash'
import { ModelType } from 'api/moreCast2API'

interface WeatherModelDropdownProps {
  label?: string
  selectedModelType: ModelType
  weatherModelOptions: ModelType[]
  setSelectedModelType: React.Dispatch<React.SetStateAction<ModelType>>
}

const WeatherModelDropdown = (props: WeatherModelDropdownProps) => {
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(props.selectedModelType, value)) {
      props.setSelectedModelType(value)
    }
  }

  return (
    <Autocomplete
      sx={{ minWidth: 280 }}
      data-testid={`weather-model-dropdown`}
      disableClearable
      options={props.weatherModelOptions}
      renderInput={params => (
        <TextField {...params} label={props.label ? props.label : 'Select Default Weather Model'} variant="outlined" />
      )}
      onChange={changeHandler}
      isOptionEqualToValue={(option, value) => isEqual(option, value)}
      value={props.selectedModelType}
    />
  )
}

export default React.memo(WeatherModelDropdown)
