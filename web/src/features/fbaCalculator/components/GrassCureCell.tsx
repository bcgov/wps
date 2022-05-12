import { TextField, Tooltip } from '@mui/material'
import { ClassNameMap } from '@mui/styles'
import { FBATableRow } from 'features/fbaCalculator/RowManager'
import { buildUpdatedNumberRow, updateFBARow } from 'features/fbaCalculator/tableState'
import { isGrassCureInvalid } from 'features/fbaCalculator/validation'
import { isEqual, isNull, isUndefined } from 'lodash'
import React, { ChangeEvent, useEffect, useState } from 'react'

export interface GrassCureCellProps {
  inputRows: FBATableRow[]
  updateRow: (rowId: number, updatedRow: FBATableRow, dispatchRequest?: boolean) => void
  classNameMap: ClassNameMap<'grassCure'>
  value: number | undefined
  disabled: boolean
  rowId: number
}

const GrassCureProps = (props: GrassCureCellProps) => {
  const [lastRequestedGrassCure, setLastRequestedGrassCure] = useState(props.value)
  const [grassCurePercentage, setGrassCurePercentage] = useState(props.value)
  useEffect(() => setGrassCurePercentage(props.value), [props])

  const changeHandler = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const stringInput = String(event.target.value)
    const numberInput = parseInt(stringInput)
    if (isUndefined(stringInput) || isNull(stringInput) || isNaN(numberInput) || stringInput.length <= 3) {
      setGrassCurePercentage(parseInt(event.target.value))
    }
  }

  const handlePossibleUpdate = () => {
    if (!isEqual(lastRequestedGrassCure, grassCurePercentage)) {
      setLastRequestedGrassCure(grassCurePercentage)
      const updatedRow = buildUpdatedNumberRow(props.inputRows[props.rowId], 'grassCure', grassCurePercentage)
      const dispatchRequest = !isGrassCureInvalid(updatedRow)
      updateFBARow(
        props.inputRows,
        props.updateRow,
        props.rowId,
        'grassCure',
        grassCurePercentage,
        buildUpdatedNumberRow,
        dispatchRequest
      )
    }
  }

  const enterHandler = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Enter') {
      handlePossibleUpdate()
    }
  }

  const hasError = isGrassCureInvalid(props.inputRows[props.rowId])

  return (
    <Tooltip title="Cannot exceed 100" aria-label="cannot-exceed-100">
      <TextField
        data-testid={`grassCureInput-fba-${props.rowId}`}
        type="number"
        inputMode="numeric"
        className={props.classNameMap.grassCure}
        size="small"
        variant="outlined"
        inputProps={{ min: 0, max: 100 }}
        onChange={changeHandler}
        onBlur={handlePossibleUpdate}
        onKeyDown={enterHandler}
        value={grassCurePercentage ? grassCurePercentage : ''}
        disabled={props.disabled}
        error={hasError}
      />
    </Tooltip>
  )
}

export default React.memo(GrassCureProps)
