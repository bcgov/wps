import { TableCell } from '@mui/material'
import { styled } from '@mui/material/styles'
import { UNSELECTED_STATION_COLOR } from 'app/theme'
import React from 'react'

export const SelectedIntensityGroupCell = styled(TableCell, { name: 'intensityGroupCell' })({
  width: 30,
  textAlign: 'center'
})

export const UnSelectedIntensityGroupCell = styled(TableCell)({
  color: UNSELECTED_STATION_COLOR,
  width: 30,
  textAlign: 'center'
})

export interface IntensityGroupCellProps {
  testid: string | undefined
  value: number | undefined
  error: boolean
  selected: boolean
}

const IntensityGroupCell = (props: IntensityGroupCellProps) => {
  return !props.selected && !props.error && props.value ? (
    <UnSelectedIntensityGroupCell data-testid={props.testid}>
      {props.error ? '' : props.value}
    </UnSelectedIntensityGroupCell>
  ) : (
    <SelectedIntensityGroupCell data-testid={props.testid}>{props.error ? '' : props.value}</SelectedIntensityGroupCell>
  )
}

export default React.memo(IntensityGroupCell)
