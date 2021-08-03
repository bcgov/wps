import { TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { Autocomplete } from '@material-ui/lab'
import {
  FBAInputGridProps,
  GridMenuOption
} from 'features/fbaCalculator/components/FBAInputGrid'
import { buildUpdatedOptionRow, updateFBARow } from 'features/fbaCalculator/tableState'
import { isEqual } from 'lodash'
import React from 'react'

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
  // eslint-disable-next-line
  const changeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    updateFBARow(
      props.fbaInputGridProps,
      props.rowId,
      'fuelType',
      value,
      buildUpdatedOptionRow
    )
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
      value={props.value}
      onBlur={props.fbaInputGridProps.autoUpdateHandler}
      onKeyDown={event => {
        if (event.key === 'Enter') {
          event.preventDefault()
          props.fbaInputGridProps.autoUpdateHandler()
        }
      }}
    />
  )
}

export default React.memo(FuelTypeCell)
