import { TableCell, Tooltip } from '@material-ui/core'
import ErrorOutlineIcon from '@material-ui/icons/ErrorOutline'
import { createMuiTheme, ThemeProvider } from '@material-ui/core/styles'
import React from 'react'

export interface GrassCureCellProps {
  value: string | number | undefined
}

const adjustedTheme = createMuiTheme({
  overrides: {
    MuiSvgIcon: {
      root: {
        fill: '#D8292F'
      }
    }
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
  return (
    <TableCell>
      {props.value ? (
        props.value
      ) : (
        <ThemeProvider theme={adjustedTheme}>
          <Tooltip
            title={toolTipElement}
            aria-label={`${toolTipFirstLine} \n ${toolTipSecondLine}`}
          >
            <ErrorOutlineIcon></ErrorOutlineIcon>
          </Tooltip>
        </ThemeProvider>
      )}
    </TableCell>
  )
}

export default React.memo(GrassCureProps)
