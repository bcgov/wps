import { createTheme, makeStyles, ThemeProvider, Tooltip } from '@material-ui/core'
import ErrorOutlineIcon from '@material-ui/icons/ErrorOutline'
import { fireTableStyles } from 'app/theme'
import React from 'react'

export interface ErrorIconWithTooltipProps {
  testId?: string
  tooltipElement: JSX.Element
  tooltipAriaText: string[]
}

const useStyles = makeStyles({
  alignErrorIcon: {
    ...fireTableStyles.planningArea,
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
        <div className={classes.alignErrorIcon}>
          <ErrorOutlineIcon data-testid={props.testId}></ErrorOutlineIcon>
        </div>
      </Tooltip>
    </ThemeProvider>
  )
}

export default React.memo(ErrorIconWithTooltip)
