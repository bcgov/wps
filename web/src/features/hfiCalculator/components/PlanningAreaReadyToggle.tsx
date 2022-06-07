import { createTheme, ThemeProvider, StyledEngineProvider, Tooltip, IconButton } from '@mui/material'
import ToggleOffOutlinedIcon from '@mui/icons-material/ToggleOffOutlined'
import ToggleOnOutlinedIcon from '@mui/icons-material/ToggleOnOutlined'
import React from 'react'
import { ReadyPlanningAreaDetails } from 'api/hfiCalculatorAPI'
import { isUndefined } from 'lodash'

export interface PlanningAreaReadyToggleProps {
  disabled: boolean
  loading: boolean
  readyDetails?: ReadyPlanningAreaDetails
  toggleReady: (planningAreaId: number, hfiRequestId: number) => void
}

const PlanningAreaReadyToggle = ({ disabled, loading, readyDetails, toggleReady }: PlanningAreaReadyToggleProps) => {
  const toggleReadyTheme = createTheme({
    components: {
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            fontSize: 14
          }
        }
      }
    }
  })
  const toolTipText = `Marked ready by ${readyDetails?.update_user} at ${readyDetails?.update_timestamp.toISO()}`
  return (
    <IconButton
      aria-label="hfi-toggle-ready"
      data-testid="hfi-toggle-ready"
      disabled={disabled || loading}
      onClick={() => {
        if (!isUndefined(readyDetails)) {
          toggleReady(readyDetails.planning_area_id, readyDetails.hfi_request_id)
        }
      }}
    >
      {readyDetails?.ready ? (
        <StyledEngineProvider injectFirst>
          <ThemeProvider theme={toggleReadyTheme}>
            <Tooltip title={toolTipText} aria-label={toolTipText}>
              <ToggleOnOutlinedIcon fontSize="large" color="success" />
            </Tooltip>
          </ThemeProvider>
        </StyledEngineProvider>
      ) : (
        <ToggleOffOutlinedIcon fontSize="large" />
      )}
    </IconButton>
  )
}

export default React.memo(PlanningAreaReadyToggle)
