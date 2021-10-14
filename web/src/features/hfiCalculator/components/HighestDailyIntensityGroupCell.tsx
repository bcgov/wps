import { makeStyles, TableCell } from '@material-ui/core'
import { StationDaily } from 'api/hfiCalculatorAPI'
import { fireTableStyles } from 'app/theme'
import { isUndefined } from 'lodash'
import React from 'react'

export interface HighestDailyIntensityGroupCellProps {
  dailies: StationDaily[] | undefined
}

const useStyles = makeStyles({
  ...fireTableStyles
})
const HighestDailyIntensityGroupCell = (props: HighestDailyIntensityGroupCellProps) => {
  const classes = useStyles()

  const intensityGroups: number[] = isUndefined(props.dailies)
    ? []
    : props.dailies.map(daily => daily.intensity_group)
  const highestIntensityGroup = Math.max(...intensityGroups)
  return (
    <TableCell
      data-testid={'highest-intensity-group'}
      className={classes.sectionSeparatorBorder}
    >
      {highestIntensityGroup ? highestIntensityGroup : ''}
    </TableCell>
  )
}

export default React.memo(HighestDailyIntensityGroupCell)
