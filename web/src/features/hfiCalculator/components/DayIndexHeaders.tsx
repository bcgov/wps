import { TableCell, styled } from '@mui/material'
import { range } from 'lodash'
import React from 'react'

export interface DayIndexHeadersProps {
  numPrepDays: number
}

const ROSDayIndexHeaderCell = styled(TableCell, {
  shouldForwardProp: prop => prop !== 'showBorder'
})<{ showBorder: boolean }>(({ showBorder }) => ({
  borderLeft: showBorder ? '1px solid #C4C4C4' : undefined
}))

const DayIndexHeaders = (props: DayIndexHeadersProps) => {
  return (
    <React.Fragment>
      {range(props.numPrepDays).map(i => (
        <React.Fragment key={i}>
          <ROSDayIndexHeaderCell data-testid={`ros-header-${i}`} showBorder={i > 0}>
            {' '}
            ROS
            <br />
            (m/min)
          </ROSDayIndexHeaderCell>
          <TableCell data-testid={`hfi-header-${i}`}>HFI</TableCell>
          <TableCell data-testid={`fig-header-${i}`}>
            M /
            <br />
            FIG
          </TableCell>
          <TableCell data-testid={`fire-starts-header-${i}`}>
            Fire
            <br />
            Starts
          </TableCell>
          <TableCell data-testid={`prep-level-header-${i}`}>
            Prep
            <br />
            Level
          </TableCell>
        </React.Fragment>
      ))}
    </React.Fragment>
  )
}

export default React.memo(DayIndexHeaders)
