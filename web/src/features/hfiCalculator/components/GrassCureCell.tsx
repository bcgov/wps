import { TableCell } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import React from 'react'
import { isNull } from 'lodash'
import { fireTableStyles } from 'app/theme'
import ErrorIconWithTooltip from 'features/hfiCalculator/components/ErrorIconWithTooltip'

export interface GrassCureCellProps {
  value: number | null | undefined
  isGrassFuelType: boolean
  className: string | undefined
  selected: boolean
}

const useStyles = makeStyles({
  unselectedStation: { ...fireTableStyles.unselectedStation }
})

const toolTipFirstLine = 'Grass Cure % not defined in WFWX.'
const toolTipSecondLine = 'Cannot calculate ROS, Fire Size/Type, HFI, FIG.'
const toolTipElement = (
  <div>
    {toolTipFirstLine} <br />
    {toolTipSecondLine}
  </div>
)

const GrassCureProps = (props: GrassCureCellProps) => {
  const classes = useStyles()
  return isNull(props.value) && props.isGrassFuelType ? (
    <TableCell className={props.className}>
      <ErrorIconWithTooltip
        testId={`grass-cure-error`}
        isDataCell={true}
        tooltipElement={toolTipElement}
        tooltipAriaText={[toolTipFirstLine, toolTipSecondLine]}
      />
    </TableCell>
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
