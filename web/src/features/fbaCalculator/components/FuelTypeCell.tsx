import { TextField, Autocomplete } from '@mui/material'
import { GridMenuOption } from 'features/fbaCalculator/components/FBATable'
import { FBATableRow } from 'features/fbaCalculator/RowManager'
import { buildUpdatedOptionRow, updateFBARow } from 'features/fbaCalculator/tableState'
import { isGrassCureInvalid } from 'features/fbaCalculator/validation'
import { isEqual } from 'lodash'
import React, { useEffect, useState } from 'react'

interface FuelTypeCellProps {
  fuelTypeOptions: GridMenuOption[]
  inputRows: FBATableRow[]
  updateRow: (rowId: number, updatedRow: FBATableRow, dispatchRequest?: boolean) => void
  value: GridMenuOption | null
  disabled: boolean
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
      const updatedRow = buildUpdatedOptionRow(props.inputRows[props.rowId], 'fuelType', value)
      const dispatchRequest = !isGrassCureInvalid(updatedRow)
      updateFBARow(
        props.inputRows,
        props.updateRow,
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
      sx={{ minWidth: 220 }}
      data-testid={`fuel-type-dropdown-fba-${props.rowId}`}
      autoHighlight={true}
      autoSelect={true}
      options={props.fuelTypeOptions}
      isOptionEqualToValue={(option, value) => isEqual(option, value)}
      getOptionLabel={option => option?.label}
      renderInput={params => (
        <TextField {...params} label={props.value ? '' : emptyLabel} variant="outlined" size="small" />
      )}
      onChange={changeHandler}
      disabled={props.disabled}
      value={selectedFuelType}
    />
  )
}

export default React.memo(FuelTypeCell)
