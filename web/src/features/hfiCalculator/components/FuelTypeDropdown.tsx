import { makeStyles, TextField } from '@material-ui/core'
import { WeatherStation } from 'api/hfiCalcAPI'
import { Autocomplete } from '@material-ui/lab'
import { StationInfo } from 'features/hfiCalculator/slices/hfiCalculatorSlice'
import { isEqual, isNull } from 'lodash'
import React from 'react'

export interface FuelTypeDropDownProps {
  station: WeatherStation
  stationInfo?: StationInfo
  setFuelType: (code: number, fuelTypeId: number) => void
}

const useStyles = makeStyles({
  dropdownClass: {
    width: '96px'
  }
})

const FuelTypeDropDown = ({
  station,
  stationInfo,
  setFuelType
}: FuelTypeDropDownProps) => {
  const classes = useStyles()
  // TODO: Wire up fuel type list
  const fuelTypes = []
  for (let i = 0; i < 100; i++) {
    fuelTypes.push(i)
  }
  // TODO: Wire up permissions
  if (stationInfo) {
    return (
      <Autocomplete
        className={classes.dropdownClass}
        disableClearable
        autoHighlight
        autoSelect
        options={fuelTypes}
        getOptionSelected={(option, value) => isEqual(option, value)}
        getOptionLabel={option => String(option)}
        renderInput={params => (
          <TextField {...params} variant="outlined" value={stationInfo.fuel_type_id} />
        )}
        value={stationInfo.fuel_type_id}
        onChange={(_, value) => {
          if (!isNull(value)) {
            setFuelType(station.code, value)
          }
        }}
      />
    )
  }
  return <div></div>
}

export default React.memo(FuelTypeDropDown)
