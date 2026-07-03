import type { GridRenderCellParams } from '@mui/x-data-grid-pro'
import { isNil } from 'lodash'
import React from 'react'
import { useSelector } from 'react-redux'
import ValidatedCell from '@/features/moreCast2/components/ValidatedCell'
import { selectMorecastRequiredInputEmpty } from '@/features/moreCast2/slices/validInputSlice'

interface ValidatedForecastCellProps {
  disabled: boolean
  label: string
  value: Pick<GridRenderCellParams, 'formattedValue'>
  validator?: (value: string) => string
}

const ValidatedForecastCell = ({ disabled, label, value, validator }: ValidatedForecastCellProps) => {
  const isRequiredInputEmpty = useSelector(selectMorecastRequiredInputEmpty)
  const invalid = validator ? validator(value as string) : ''
  const error = (isRequiredInputEmpty.empty && (value as string) === '') || isNil(value) || invalid !== ''
  return <ValidatedCell disabled={disabled} label={label} value={value} error={error} invalid={invalid} />
}

export default React.memo(ValidatedForecastCell)
