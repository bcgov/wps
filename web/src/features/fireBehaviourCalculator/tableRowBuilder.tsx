import { Checkbox, TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import {
  GridMenuOption,
  FBCInputRow,
  FBCInputGridProps
} from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import { grassCureNotSetForGrassType } from 'features/fireBehaviourCalculator/validation'
import { find, isEqual } from 'lodash'
import React, { ChangeEvent } from 'react'

const buildAutocompleteCell = (
  options: GridMenuOption[],
  emptyLabel: string,
  cell: { column: { id: string }; value: GridMenuOption },
  // eslint-disable-next-line
  changeHandler: (event: React.ChangeEvent<{}>, value: any) => void
) => (
  <Autocomplete
    options={options}
    getOptionSelected={(option, value) => isEqual(option, value)}
    getOptionLabel={option => option?.label}
    style={{ width: 300 }}
    renderInput={params => (
      <TextField {...params} label={cell.value ? '' : emptyLabel} variant="outlined" />
    )}
    onChange={changeHandler}
    value={cell.value}
  />
)

// eslint-disable-next-line
const buildUpdatedOptionRow = (rowToUpdate: FBCInputRow, field: string, value: any) => {
  return {
    ...rowToUpdate,
    ...{
      [field as keyof FBCInputRow]: (value as GridMenuOption)?.value
    }
  }
}

// eslint-disable-next-line
const buildUpdatedNumberRow = (rowToUpdate: FBCInputRow, field: string, value: any) => {
  return {
    ...rowToUpdate,
    ...{
      [field as keyof FBCInputRow]: parseInt(value)
    }
  }
}

export const buildRowCell = (
  props: FBCInputGridProps,
  cell: {
    column: { id: string }
    value: GridMenuOption
  },
  field: string,
  rowId: number
): JSX.Element => {
  const updateFBCRow = (
    props: FBCInputGridProps,
    rowId: number,
    field: string,
    // eslint-disable-next-line
    value: any,
    updatedRowBuilder: (
      rowToUpdate: FBCInputRow,
      field: string,
      value: GridMenuOption | number
    ) => FBCInputRow
  ) => {
    const rowToUpdate = find(props.rows, ['id', rowId])
    if (rowToUpdate) {
      const updatedRow = updatedRowBuilder(rowToUpdate, field, value)
      props.updateRow(rowId, updatedRow)
    }
  }
  // eslint-disable-next-line
  const autoCompleteChangeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    updateFBCRow(props, rowId, field, value, buildUpdatedOptionRow)
  }

  const numberFieldChangeHandler = (
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    updateFBCRow(props, rowId, field, parseInt(event.target.value), buildUpdatedNumberRow)
  }

  if (cell.column.id === 'weatherStation' || cell.column.id === 'fuelType') {
    const emptyLabel =
      cell.column.id === 'weatherStation' ? 'Select a station' : 'Select a fuel type'
    const options =
      cell.column.id === 'weatherStation' ? props.stationOptions : props.fuelTypeOptions
    return buildAutocompleteCell(options, emptyLabel, cell, autoCompleteChangeHandler)
  }

  if (cell.column.id === 'select') {
    const selectedSet = new Set(props.selected)
    return (
      <Checkbox
        color="primary"
        checked={selectedSet.has(rowId)}
        onClick={() => {
          if (selectedSet.has(rowId)) {
            // Checked, toggle check off
            selectedSet.delete(rowId)
          } else {
            // Unchecked, toggle check on
            selectedSet.add(rowId)
          }
          props.updateSelected(Array.from(selectedSet))
        }}
      />
    )
  }

  const errorState =
    cell.column.id === 'grassCure' && grassCureNotSetForGrassType(props.rows[rowId])

  return (
    <TextField
      type="number"
      variant="outlined"
      inputProps={{ min: 0 }}
      onChange={numberFieldChangeHandler}
      value={cell.value}
      error={errorState}
    />
  )
}
