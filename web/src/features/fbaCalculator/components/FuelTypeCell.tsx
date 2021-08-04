import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { Autocomplete } from '@material-ui/lab'
import {
  FBAInputGridProps,
  GridMenuOption
} from 'features/fbaCalculator/components/FBAInputGrid'
import { buildUpdatedOptionRow, updateFBARow } from 'features/fbaCalculator/tableState'
import { isEqual } from 'lodash'
import React, { useState } from 'react'

interface FuelTypeCellProps {
  fbaInputGridProps: Pick<
    FBAInputGridProps,
    'fuelTypeOptions' | 'inputRows' | 'updateRow' | 'autoUpdateHandler'
  >
  classNameMap: ClassNameMap<'fuelType'>
  value: GridMenuOption | null
  rowId: number
}
const emptyLabel = 'Select a fuel type'
const FuelTypeCell = (props: FuelTypeCellProps) => {
  const [selectedFuelType, setSelectedFuelType] = useState(props.value)

  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(selectedFuelType, value)) {
      setSelectedFuelType(value)
      updateFBARow(
        props.fbaInputGridProps,
        props.rowId,
        'fuelType',
        value,
        buildUpdatedOptionRow
      )
    }
  }
  return (
    <Autocomplete
      options={props.fbaInputGridProps.fuelTypeOptions}
      className={props.classNameMap.fuelType}
      getOptionSelected={(option, value) => isEqual(option, value)}
      getOptionLabel={option => option?.label}
      renderInput={params => (
        <TextField
          {...params}
          label={props.value ? '' : emptyLabel}
          variant="outlined"
          size="small"
        />
      )}
      onChange={changeHandler}
      value={selectedFuelType}
    />
  )
}

export default React.memo(FuelTypeCell)
