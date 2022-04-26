import { TableCell } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { fireTableStyles } from 'app/theme'
import { range } from 'lodash'
import React from 'react'

const useStyles = makeStyles({
  ...fireTableStyles
})

export interface DayIndexHeadersProps {
  numPrepDays: number
}
const DayIndexHeaders = (props: DayIndexHeadersProps) => {
  const classes = useStyles()
  return (
    <React.Fragment>
      {range(props.numPrepDays).map(i => (
        <React.Fragment key={i}>
          <TableCell
            data-testid={`ros-header-${i}`}
            className={`${i > 0 ? classes.sectionSeparatorBorder : undefined}`}
          >
            ROS
            <br />
            (m/min)
          </TableCell>
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
