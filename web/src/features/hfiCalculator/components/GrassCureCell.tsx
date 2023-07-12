import { TableCell } from '@mui/material'
import { styled } from '@mui/material/styles'
import React from 'react'
import { isNull } from 'lodash'
import { UNSELECTED_STATION_COLOR } from 'app/theme'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'

const DefaultGrassFuelCell = styled(TableCell)({
  borderBottom: 'none'
})

const UnselectedGrassFuelCell = styled(TableCell)({
  color: UNSELECTED_STATION_COLOR
})

export interface GrassCureCellProps {
  value: number | null | undefined
  isGrassFuelType: boolean
  className: string | undefined
  selected: boolean
}

const toolTipFirstLine = 'Grass Cure % not defined in WFWX.'
const toolTipSecondLine = 'Cannot calculate ROS, Fire Size/Type, HFI, FIG.'
const toolTipElement = (
  <div>
    {toolTipFirstLine} <br />
    {toolTipSecondLine}
  </div>
)

const GrassCureCell = (props: GrassCureCellProps) => {
  const variablySelectedGrassFuelCell = !props.selected ? (
    <UnselectedGrassFuelCell data-testid={`grass-cure`}>{props.value}</UnselectedGrassFuelCell>
  ) : (
    <DefaultGrassFuelCell data-testid={`grass-cure`}>{props.value}</DefaultGrassFuelCell>
  )
  return isNull(props.value) && props.isGrassFuelType ? (
    <DefaultGrassFuelCell>
      <ErrorIconWithTooltip
        testId={`grass-cure-error`}
        isDataCell={true}
        tooltipElement={toolTipElement}
        tooltipAriaText={[toolTipFirstLine, toolTipSecondLine]}
      />
    </DefaultGrassFuelCell>
  ) : (
    variablySelectedGrassFuelCell
  )
}

export default React.memo(GrassCureCell)
