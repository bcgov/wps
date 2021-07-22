import { Checkbox, TextField } from '@material-ui/core'
import { ClassNameMap } from '@material-ui/core/styles/withStyles'
import { Autocomplete } from '@material-ui/lab'
import {
  GridMenuOption,
  FBCInputRow,
  FBCInputGridProps
} from 'features/fireBehaviourCalculator/components/FBCInputGrid'
import { grassCureNotSetForGrassType } from 'features/fireBehaviourCalculator/validation'
import { find, isEqual } from 'lodash'
import React, { ChangeEvent } from 'react'

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
  const rowToUpdate = find(props.inputRows, ['id', rowId])
  if (rowToUpdate) {
    const updatedRow = updatedRowBuilder(rowToUpdate, field, value)
    props.updateRow(rowId, updatedRow)
  }
}

export const buildWeatherStationCell = (
  props: FBCInputGridProps,
  classNameMap: ClassNameMap<'weatherStation'>,
  value: GridMenuOption | null,
  rowId: number
): JSX.Element => {
  // eslint-disable-next-line
  const autoCompleteChangeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    updateFBCRow(props, rowId, 'weatherStation', value, buildUpdatedOptionRow)
  }
  return buildAutocompleteCell(
    props,
    classNameMap,
    value,
    'weatherStation',
    autoCompleteChangeHandler
  )
}

export const buildFuelTypeCell = (
  props: FBCInputGridProps,
  classNameMap: ClassNameMap<'fuelType'>,
  value: GridMenuOption | null,
  rowId: number
): JSX.Element => {
  // eslint-disable-next-line
  const autoCompleteChangeHandler = (_: React.ChangeEvent<{}>, value: any | null) => {
    updateFBCRow(props, rowId, 'fuelType', value, buildUpdatedOptionRow)
  }
  return buildAutocompleteCell(
    props,
    classNameMap,
    value,
    'fuelType',
    autoCompleteChangeHandler
  )
}

export const buildGrassCureCell = (
  props: FBCInputGridProps,
  classNameMap: ClassNameMap<'grassCure'>,
  value: number | undefined,
  rowId: number
): JSX.Element => {
  const numberFieldChangeHandler = (
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    updateFBCRow(
      props,
      rowId,
      'grassCure',
      parseInt(event.target.value),
      buildUpdatedNumberRow
    )
  }

  return buildNumberInputCell(
    value,
    'grassCure',
    props,
    classNameMap,
    rowId,
    numberFieldChangeHandler
  )
}

export const buildWindSpeedCell = (
  props: FBCInputGridProps,
  classNameMap: ClassNameMap<'windSpeed'>,
  value: number | undefined,
  rowId: number
): JSX.Element => {
  const numberFieldChangeHandler = (
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    updateFBCRow(
      props,
      rowId,
      'windSpeed',
      parseInt(event.target.value),
      buildUpdatedNumberRow
    )
  }

  return buildNumberInputCell(
    value,
    'windSpeed',
    props,
    classNameMap,
    rowId,
    numberFieldChangeHandler
  )
}

const buildAutocompleteCell = (
  props: FBCInputGridProps,
  autocompleteClasses: Partial<ClassNameMap<'weatherStation' | 'fuelType'>>,
  value: GridMenuOption | null,
  field: string,
  // eslint-disable-next-line
  changeHandler: (event: React.ChangeEvent<{}>, value: any) => void
): JSX.Element => {
  const emptyLabel =
    field === 'weatherStation' ? 'Select a station' : 'Select a fuel type'
  const options =
    field === 'weatherStation' ? props.stationOptions : props.fuelTypeOptions
  const componentClass =
    field === 'weatherStation'
      ? autocompleteClasses.weatherStation
      : autocompleteClasses.fuelType
  return (
    <Autocomplete
      options={options}
      className={componentClass}
      getOptionSelected={(option, value) => isEqual(option, value)}
      getOptionLabel={option => option?.label}
      renderInput={params => (
        <TextField
          {...params}
          label={value ? '' : emptyLabel}
          variant="outlined"
          size="small"
        />
      )}
      onChange={changeHandler}
      value={value}
    />
  )
}

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

export const buildSelectCheckboxCell = (
  props: FBCInputGridProps,
  rowId: number
): JSX.Element => {
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
const buildNumberInputCell = (
  value: number | undefined,
  field: string,
  props: FBCInputGridProps,
  numberInputClasses: Partial<ClassNameMap<'grassCure' | 'windSpeed'>>,
  rowId: number,
  numberFieldChangeHandler: (
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => void
): JSX.Element => {
  const errorState =
    field === 'grassCure' && grassCureNotSetForGrassType(props.inputRows[rowId])

  const componentClass =
    field === 'grassCure' ? numberInputClasses.grassCure : numberInputClasses.windSpeed

  return (
    <TextField
      type="number"
      className={componentClass}
      size="small"
      variant="outlined"
      inputProps={{ min: 0, maxLength: 4, size: 4 }}
      onChange={numberFieldChangeHandler}
      value={value}
      error={errorState}
    />
  )
}
