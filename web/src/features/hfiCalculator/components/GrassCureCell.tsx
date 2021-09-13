import { TableCell, Tooltip } from '@material-ui/core'
import ErrorOutlineIcon from '@material-ui/icons/ErrorOutline'
import { createTheme, makeStyles, ThemeProvider } from '@material-ui/core/styles'
import React from 'react'
import { isNull } from 'lodash'

export interface GrassCureCellProps {
  value: number | null | undefined
  isGrassFuelType: boolean
  className: string | undefined
  selected: boolean
}

const errorIconTheme = createTheme({
  overrides: {
    MuiSvgIcon: {
      root: {
        fill: '#D8292F'
      }
    }
  }
})

const useStyles = makeStyles({
  unselectedStation: {
    color: 'rgba(0,0,0,0.54)'
  }
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
      <ThemeProvider theme={errorIconTheme}>
        <Tooltip
          title={toolTipElement}
          aria-label={`${toolTipFirstLine} \n ${toolTipSecondLine}`}
        >
          <ErrorOutlineIcon data-testid={`grass-cure-error`}></ErrorOutlineIcon>
        </Tooltip>
      </ThemeProvider>
    </TableCell>
  ) : (
    <TableCell
      className={`${!props.selected ? classes.unselectedStation : undefined} ${
        props.className
      } `}
      data-testid={`grass-cure`}
    >
      {props.value}
    </TableCell>
  )
}

export default React.memo(GrassCureProps)
