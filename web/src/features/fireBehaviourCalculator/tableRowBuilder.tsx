import { TextField } from '@material-ui/core'
import { Autocomplete } from '@material-ui/lab'
import { find, isEqual } from 'lodash'
import React, { ChangeEvent } from 'react'
import { GridMenuOption, FBCInputRow } from './components/FBCInputGrid'
import { FBCInputGridProps } from './components/FBCInputGrid'

const buildWeatherStationCell = (
  options: GridMenuOption[],
  emptyLabel: string,
  cell: { column: { id: string }; value: GridMenuOption },
  changeHandler: (event: React.ChangeEvent<{}>, value: any) => void
) => (
  <Autocomplete
    options={options}
    getOptionSelected={(option, value) => isEqual(option, value)}
    getOptionLabel={option => option?.label}
    style={{ width: 300 }}
    renderInput={params => <TextField {...params} label={cell.value ? '' : emptyLabel} />}
    onChange={changeHandler}
    value={cell.value}
  />
)

function buildUpdatedOptionRow(rowToUpdate: FBCInputRow, field: string, value: any) {
  return {
    ...rowToUpdate,
    ...{
      [field as keyof FBCInputRow]: (value as GridMenuOption)?.value
    }
  }
}

function buildUpdatedNumberRow(rowToUpdate: FBCInputRow, field: string, value: any) {
  return {
    ...rowToUpdate,
    ...{
      [field as keyof FBCInputRow]: parseInt(value)
    }
  }
}

export const buildRowCell = (
  props: FBCInputGridProps,
  cell: { column: { id: string }; value: GridMenuOption },
  field: string,
  rowId: number
) => {
  const updateFBCRow = (
    props: FBCInputGridProps,
    rowId: number,
    field: string,
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
    return buildWeatherStationCell(options, emptyLabel, cell, autoCompleteChangeHandler)
  }

  return (
    <TextField type="number" onChange={numberFieldChangeHandler} value={cell.value} />
  )
}
