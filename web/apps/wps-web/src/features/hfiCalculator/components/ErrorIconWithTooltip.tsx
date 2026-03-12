import { createTheme, StyledEngineProvider, ThemeProvider, Tooltip } from '@mui/material'
import { styled } from '@mui/material/styles'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import { BACKGROUND_COLOR, PLANNING_AREA } from 'app/theme'
import { isUndefined } from 'lodash'
import React from 'react'

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

export const DataCellIcon = styled('div')({
  paddingTop: '10px',
  textAlign: 'center'
})

const PlanningAreaIcon = styled('div')({
  ...BACKGROUND_COLOR,
  ...PLANNING_AREA,
  paddingTop: '10px',
  textAlign: 'center'
})

const ErrorIconWithTooltip = (props: ErrorIconWithTooltipProps) => {
  const icon =
    !props.isDataCell || isUndefined(props.isDataCell) ? (
      <PlanningAreaIcon>
        <ErrorOutlineIcon data-testid={props.testId}></ErrorOutlineIcon>
      </PlanningAreaIcon>
    ) : (
      <DataCellIcon>
        <ErrorOutlineIcon data-testid={props.testId}></ErrorOutlineIcon>
      </DataCellIcon>
    )
  return (
    <StyledEngineProvider injectFirst>
      <ThemeProvider theme={errorIconTheme}>
        <Tooltip title={props.tooltipElement} aria-label={`${props.tooltipAriaText.join('\n')}`}>
          {icon}
        </Tooltip>
      </ThemeProvider>
    </StyledEngineProvider>
  )
}

export default React.memo(ErrorIconWithTooltip)
