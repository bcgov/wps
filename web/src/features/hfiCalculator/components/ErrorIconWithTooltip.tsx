import { createTheme, ThemeProvider, Theme, StyledEngineProvider, Tooltip } from '@mui/material'
import { styled } from '@mui/material/styles'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import { fireTableStyles } from 'app/theme'
import { isUndefined } from 'lodash'
import React from 'react'

const PREFIX = 'ErrorIconWithTooltip'

const classes = {
  planningAreaIcon: `${PREFIX}-planningAreaIcon`,
  dataCellIcon: `${PREFIX}-dataCellIcon`
}

const StyledStyledEngineProvider = styled(StyledEngineProvider)({
  [`& .${classes.planningAreaIcon}`]: {
    ...fireTableStyles.planningArea,
    paddingTop: '10px',
    textAlign: 'center'
  },
  [`& .${classes.dataCellIcon}`]: {
    paddingTop: '10px',
    textAlign: 'center'
  }
})

declare module '@mui/styles/defaultTheme' {
  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface DefaultTheme extends Theme {}
}

export interface ErrorIconWithTooltipProps {
  testId?: string
  tooltipElement: JSX.Element
  tooltipAriaText: string[]
  isDataCell?: boolean
}

const errorIconTheme = createTheme({
  components: {
    MuiSvgIcon: {
      styleOverrides: {
        root: {
          fill: '#D8292F'
        }
      }
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          fontSize: 14
        }
      }
    }
  }
})

const ErrorIconWithTooltip = (props: ErrorIconWithTooltipProps) => {
  return (
    <StyledStyledEngineProvider injectFirst>
      <ThemeProvider theme={errorIconTheme}>
        <Tooltip title={props.tooltipElement} aria-label={`${props.tooltipAriaText.join('\n')}`}>
          <div
            className={
              !props.isDataCell || isUndefined(props.isDataCell) ? classes.planningAreaIcon : classes.dataCellIcon
            }
          >
            <ErrorOutlineIcon data-testid={props.testId}></ErrorOutlineIcon>
          </div>
        </Tooltip>
      </ThemeProvider>
    </StyledStyledEngineProvider>
  )
}

export default React.memo(ErrorIconWithTooltip)
