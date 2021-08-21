import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { Autocomplete } from '@material-ui/lab'
import {
  FBAInputGridProps,
  GridMenuOption
} from 'features/fbaCalculator/components/FBATable'
import { buildUpdatedOptionRow, updateFBARow } from 'features/fbaCalculator/tableState'
import { isGrassCureInvalid } from 'features/fbaCalculator/validation'
import { isEqual } from 'lodash'
import React, { useEffect, useState } from 'react'

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
  useEffect(() => setSelectedFuelType(props.value), [props])

  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    if (!isEqual(selectedFuelType, value)) {
      setSelectedFuelType(value)
      const updatedRow = buildUpdatedOptionRow(
        props.fbaInputGridProps.inputRows[props.rowId],
        'fuelType',
        value
      )
      const dispatchRequest = !isGrassCureInvalid(updatedRow)
      updateFBARow(
        props.fbaInputGridProps,
        props.rowId,
        'fuelType',
        value,
        buildUpdatedOptionRow,
        dispatchRequest
      )
    }
  }
  return (
    <Autocomplete
      data-testid={`fuel-type-dropdown-${props.rowId}`}
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
