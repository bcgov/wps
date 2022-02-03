import { createTheme, makeStyles, ThemeProvider, Tooltip } from '@material-ui/core'
import ErrorOutlineIcon from '@material-ui/icons/ErrorOutline'
import { fireTableStyles } from 'app/theme'
import { isUndefined } from 'lodash'
import React from 'react'

export interface ErrorIconWithTooltipProps {
  testId?: string
  tooltipElement: JSX.Element
  tooltipAriaText: string[]
  isDataCell?: boolean
}

const useStyles = makeStyles({
  planningAreaIcon: {
    ...fireTableStyles.planningArea,
    paddingTop: '10px',
    textAlign: 'center'
  },
  dataCellIcon: {
    paddingTop: '10px',
    textAlign: 'center'
  }
})

const errorIconTheme = createTheme({
  overrides: {
    MuiSvgIcon: {
      root: {
        fill: '#D8292F'
      }
    },
    MuiTooltip: {
      tooltip: {
        fontSize: 14
      }
    }
  }
})

const ErrorIconWithTooltip = (props: ErrorIconWithTooltipProps) => {
  const classes = useStyles()
  return (
    <ThemeProvider theme={errorIconTheme}>
      <Tooltip
        title={props.tooltipElement}
        aria-label={`${props.tooltipAriaText.join('\n')}`}
      >
        <div
          className={
            !props.isDataCell || isUndefined(props.isDataCell)
              ? classes.planningAreaIcon
              : classes.dataCellIcon
          }
        >
          <ErrorOutlineIcon data-testid={props.testId}></ErrorOutlineIcon>
        </div>
      </Tooltip>
    </ThemeProvider>
  )
}

export default React.memo(ErrorIconWithTooltip)
