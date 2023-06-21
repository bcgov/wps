import { TableCell } from '@mui/material'
import { styled } from '@mui/material/styles'
import React from 'react'
import { isNull } from 'lodash'
import { fireTableStyles } from 'app/theme'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'

const PREFIX = 'GrassCureCell'

const classes = {
  unselectedStation: `${PREFIX}-unselectedStation`
}

const StyledTableCell = styled(TableCell)({
  [`& .${classes.unselectedStation}`]: { ...fireTableStyles.unselectedStation }
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

const GrassCureProps = (props: GrassCureCellProps) => {
  return isNull(props.value) && props.isGrassFuelType ? (
    <StyledTableCell className={props.className}>
      <ErrorIconWithTooltip
        testId={`grass-cure-error`}
        isDataCell={true}
        tooltipElement={toolTipElement}
        tooltipAriaText={[toolTipFirstLine, toolTipSecondLine]}
      />
    </StyledTableCell>
  ) : (
    <TableCell
      className={`${!props.selected ? classes.unselectedStation : undefined} ${props.className} `}
      data-testid={`grass-cure`}
    >
      {props.value}
    </TableCell>
  )
}

export default React.memo(GrassCureProps)
