import { TableCell } from '@material-ui/core'
import React from 'react'

export interface MeanIntensityGroupWeeklyRollupProps {
  testid: string | undefined
}

const MeanIntensityGroupWeeklyRollup = (props: MeanIntensityGroupWeeklyRollupProps) => {
  return <TableCell data-testid={props.testid}>0</TableCell>
}

export default React.memo(MeanIntensityGroupWeeklyRollup)
