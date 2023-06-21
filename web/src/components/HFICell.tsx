import { TableCell } from '@mui/material'
import { styled } from '@mui/material/styles'
import React from 'react'
import FixedDecimalNumberCell from 'features/fbaCalculator/components/FixedDecimalNumberCell'
import { isNull, isUndefined } from 'lodash'

const PREFIX = 'HFICell'

const classes = {
  dataRow: `${PREFIX}-dataRow`,
  orangeBorder: `${PREFIX}-orangeBorder`,
  orangeFill: `${PREFIX}-orangeFill`,
  redFill: `${PREFIX}-redFill`
}

const StyledFixedDecimalNumberCell = styled(FixedDecimalNumberCell)({
  [`& .${classes.dataRow}`]: {
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  },
  [`& .${classes.orangeBorder}`]: {
    border: 'solid 3px #FFC464',
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  },
  [`& .${classes.orangeFill}`]: {
    backgroundColor: '#FFC464',
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  },
  [`& .${classes.redFill}`]: {
    backgroundColor: '#FF6259',
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  }
})

interface HFICellProps {
  value?: number | null
  testId?: string
  className?: string
}

const HFICell = (props: HFICellProps) => {
  const getHFIStyle = (value: number | undefined | null): string => {
    if (!isUndefined(value) && !isNull(value)) {
      if (value >= 3000 && value <= 3999) {
        return classes.orangeBorder
      } else if (value > 3999 && value <= 9999) {
        return classes.orangeFill
      } else if (value > 9999) {
        return classes.redFill
      }
    }
    return classes.dataRow
  }

  const hfiStyle = getHFIStyle(props.value)

  if (isUndefined(props.value) || isNull(props.value) || isNaN(props.value)) {
    return (
      <TableCell data-testid={props.testId} className={props.className ? props.className : classes.dataRow}></TableCell>
    )
  }

  return <StyledFixedDecimalNumberCell testId={props.testId} className={hfiStyle} value={props.value} />
}

export default React.memo(HFICell)
