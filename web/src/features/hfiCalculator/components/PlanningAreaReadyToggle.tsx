import { createTheme, ThemeProvider, StyledEngineProvider, Tooltip, IconButton } from '@mui/material'
import ToggleOffOutlinedIcon from '@mui/icons-material/ToggleOffOutlined'
import ToggleOnOutlinedIcon from '@mui/icons-material/ToggleOnOutlined'
import React from 'react'
import { ReadyPlanningAreaDetails } from 'api/hfiCalculatorAPI'
import { isUndefined } from 'lodash'

export interface PlanningAreaReadyToggleProps {
  enabled: boolean
  loading: boolean
  readyDetails?: ReadyPlanningAreaDetails
  toggleReady: (planningAreaId: number) => void
}

const PlanningAreaReadyToggle = ({ enabled, loading, readyDetails, toggleReady }: PlanningAreaReadyToggleProps) => {
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
  const toolTipText = readyDetails?.ready
    ? `Marked ready by ${readyDetails?.update_user} at ${readyDetails?.update_timestamp.toISO()}`
    : ''
  return (
    <StyledEngineProvider injectFirst>
      <ThemeProvider theme={toggleReadyTheme}>
        <Tooltip data-testid="hfi-ready-tooltip" title={toolTipText} aria-label={toolTipText}>
          <span>
            <IconButton
              aria-label="hfi-toggle-ready"
              data-testid="hfi-toggle-ready"
              disabled={!enabled || loading || isUndefined(readyDetails)}
              onClick={() => {
                if (!isUndefined(readyDetails)) {
                  toggleReady(readyDetails.planning_area_id)
                }
              }}
            >
              {readyDetails?.ready ? (
                <ToggleOnOutlinedIcon fontSize="large" color="success" />
              ) : (
                <ToggleOffOutlinedIcon fontSize="large" />
              )}
            </IconButton>
          </span>
        </Tooltip>
      </ThemeProvider>
    </StyledEngineProvider>
  )
}

export default React.memo(PlanningAreaReadyToggle)
