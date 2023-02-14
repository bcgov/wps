import React from 'react'
import { TextField, Autocomplete } from '@mui/material'
import { isEqual } from 'lodash'
import { WeatherModel } from 'features/moreCast2/constants'

interface WeatherModelDropdownProps {
  selectedWeatherModel?: WeatherModel
  weatherModelOptions: WeatherModel[]
  setSelectedWeatherModel: React.Dispatch<React.SetStateAction<WeatherModel | undefined>>
}

const WeatherModelDropdown = (props: WeatherModelDropdownProps) => {
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(props.selectedWeatherModel, value)) {
      props.setSelectedWeatherModel(value)
    }
  }

  return (
    <Autocomplete
      data-testid={`weather-model-dropdown`}
      options={props.weatherModelOptions}
      getOptionLabel={option => option?.name}
      renderInput={params => <TextField {...params} label="Select Default Weather Model" variant="outlined" />}
      onChange={changeHandler}
      value={props.selectedWeatherModel || null}
    />
  )
}

export default React.memo(WeatherModelDropdown)
