import { TableCell, Tooltip } from '@material-ui/core'
import ErrorOutlineIcon from '@material-ui/icons/ErrorOutline'
import { createMuiTheme, ThemeProvider } from '@material-ui/core/styles'
import React from 'react'
import { isNull } from 'lodash'

export interface GrassCureCellProps {
  value: number | null | undefined
  isGrassFuelType: boolean
}

const errorIconTheme = createMuiTheme({
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
      {isNull(props.value) && props.isGrassFuelType ? (
        <ThemeProvider theme={errorIconTheme}>
          <Tooltip
            title={toolTipElement}
            aria-label={`${toolTipFirstLine} \n ${toolTipSecondLine}`}
          >
            <ErrorOutlineIcon></ErrorOutlineIcon>
          </Tooltip>
        </ThemeProvider>
      ) : (
        props.value
      )}
    </TableCell>
  )
}

export default React.memo(GrassCureProps)
