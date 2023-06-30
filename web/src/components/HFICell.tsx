import { TableCell } from '@mui/material'
import { styled } from '@mui/material/styles'
import React from 'react'
import FixedDecimalNumberCell from 'features/fbaCalculator/components/FixedDecimalNumberCell'
import { isNull, isUndefined } from 'lodash'

const PREFIX = 'HFICell'

const classes = {
  dataRow: `${PREFIX}-dataRow`
}

const baseStyles = {
  height: '40px',
  paddingLeft: '8px',
  paddingRight: '8px'
}

const DataCell = styled(FixedDecimalNumberCell, {
  name: `${PREFIX}-dataRow`
})(() => {
  return { ...baseStyles }
})

const OrangeBorderCell = styled(FixedDecimalNumberCell, {
  name: `${PREFIX}-orangeBorder`
})(() => {
  return { ...baseStyles, border: 'solid 3px #FFC464' }
})

const OrangeFillCell = styled(FixedDecimalNumberCell, {
  name: `${PREFIX}-orangeFill`
})(() => {
  return { ...baseStyles, backgroundColor: '#FFC464' }
})

const RedFillCell = styled(FixedDecimalNumberCell, {
  name: `${PREFIX}-redFill`
})(() => {
  return { ...baseStyles, backgroundColor: '#FF6259' }
})

interface HFICellProps {
  value?: number | null
  testId?: string
  className?: string
}

const HFICell = ({ value, testId, className }: HFICellProps) => {
  if (isUndefined(value) || isNull(value) || isNaN(value)) {
    return <TableCell data-testid={testId} className={className ? className : classes.dataRow}></TableCell>
  }
  if (value >= 3000 && value <= 3999) {
    return <OrangeBorderCell testId={testId} value={value} />
  } else if (value > 3999 && value <= 9999) {
    return <OrangeFillCell testId={testId} value={value} />
  } else if (value > 9999) {
    return <RedFillCell testId={testId} value={value} />
  }
  return <DataCell testId={testId} value={value} />
}

export default React.memo(HFICell)
