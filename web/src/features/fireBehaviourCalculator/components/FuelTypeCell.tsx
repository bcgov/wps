import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { Autocomplete } from '@material-ui/lab'
import {
  FBCInputGridProps,
  GridMenuOption
} from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import {
  buildUpdatedOptionRow,
  updateFBCRow
} from 'features/fireBehaviourCalculator/tableState'
import { isEqual } from 'lodash'
import React from 'react'

interface FuelTypeCellProps {
  fbcInputGridProps: Pick<
    FBCInputGridProps,
    'fuelTypeOptions' | 'inputRows' | 'updateRow' | 'autoUpdateHandler'
  >
  classNameMap: ClassNameMap<'fuelType'>
  value: GridMenuOption | null
  rowId: number
}
const emptyLabel = 'Select a fuel type'
const FuelTypeCell = (props: FuelTypeCellProps) => {
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    updateFBCRow(
      props.fbcInputGridProps,
      props.rowId,
      'fuelType',
      value,
      buildUpdatedOptionRow
    )
  }
  return (
    <Autocomplete
      options={props.fbcInputGridProps.fuelTypeOptions}
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
      value={props.value}
      onBlur={props.fbcInputGridProps.autoUpdateHandler}
    />
  )
}

export default React.memo(FuelTypeCell)
