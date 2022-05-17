import makeStyles from '@mui/styles/makeStyles'
import { TextField, Autocomplete } from '@mui/material'
import { FuelType, WeatherStation } from 'api/hfiCalculatorAPI'
import { isEqual, isNull } from 'lodash'
import React from 'react'

export interface FuelTypeDropdownProps {
  station: WeatherStation
  fuelTypes: FuelType[]
  selectedFuelType: FuelType
  setFuelType: (code: number, fuelTypeId: number) => void
  isRowSelected: boolean
  isSetFuelTypeEnabled: boolean
}

const useStyles = makeStyles({
  dropdownClass: {
    width: 120
  }
})

const FuelTypeDropdown = ({
  station,
  fuelTypes,
  selectedFuelType,
  setFuelType,
  isRowSelected,
  isSetFuelTypeEnabled
}: FuelTypeDropdownProps) => {
  const classes = useStyles()

  return (
    <Autocomplete
      data-testid={`fuel-type-dropdown`}
      disabled={!isRowSelected || !isSetFuelTypeEnabled}
      className={classes.dropdownClass}
      disableClearable
      autoHighlight
      autoSelect
      options={fuelTypes}
      isOptionEqualToValue={(option, value) => isEqual(option.id, value.id)}
      getOptionLabel={option => option.abbrev}
      renderInput={params => <TextField {...params} variant="outlined" value={selectedFuelType} />}
      value={selectedFuelType}
      onChange={(_, value) => {
        if (!isNull(value)) {
          setFuelType(station.code, value.id)
        }
      }}
    />
  )
}

export default React.memo(FuelTypeDropdown)
