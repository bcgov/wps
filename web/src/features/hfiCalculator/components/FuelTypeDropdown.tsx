import makeStyles from '@mui/styles/makeStyles'
import { TextField, Autocomplete } from '@mui/material'
import { FuelType, WeatherStation } from 'api/hfiCalculatorAPI'
import { StationInfo } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { isEqual, isNull } from 'lodash'
import React from 'react'

export interface FuelTypeDropDownProps {
  station: WeatherStation
  stationInfo?: StationInfo
  fuelTypes: FuelType[]
  setFuelType: (code: number, fuelTypeId: number) => void
}

const useStyles = makeStyles({
  dropdownClass: {
    width: 120
  }
})

const FuelTypeDropDown = ({
  station,
  stationInfo,
  fuelTypes,
  setFuelType
}: FuelTypeDropDownProps) => {
  const classes = useStyles()
  if (stationInfo) {
    const selectedFuelType = fuelTypes.find(
      instance => instance.id == stationInfo.fuel_type_id
    )
    return (
      <Autocomplete
        data-testid={`fuel-type-dropdown`}
        className={classes.dropdownClass}
        disableClearable
        autoHighlight
        autoSelect
        options={fuelTypes}
        isOptionEqualToValue={(option, value) => isEqual(option.id, value.id)}
        getOptionLabel={option => option.abbrev}
        renderInput={params => (
          <TextField {...params} variant="outlined" value={selectedFuelType} />
        )}
        value={selectedFuelType}
        onChange={(_, value) => {
          if (!isNull(value)) {
            setFuelType(station.code, value.id)
          }
        }}
      />
    )
  }
  return <div></div>
}

export default React.memo(FuelTypeDropDown)
