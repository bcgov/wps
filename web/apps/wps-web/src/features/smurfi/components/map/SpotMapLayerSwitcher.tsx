import { Box, Checkbox, FormControlLabel, FormGroup, Paper, Typography } from '@mui/material'
import { SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { statusToPath } from '@/features/smurfi/components/map/SpotPopup'

interface SpotMapLayerSwitcherProps {
  statusOptions: SpotRequestStatus[]
  selectedStatuses: SpotRequestStatus[]
  currentFiresVisible: boolean
  onStatusChange: (status: SpotRequestStatus, checked: boolean) => void
  onAllStatusesChange: (checked: boolean) => void
  onCurrentFiresVisibleChange: (checked: boolean) => void
}

const SpotMapLayerSwitcher = ({
  statusOptions,
  selectedStatuses,
  currentFiresVisible,
  onStatusChange,
  onAllStatusesChange,
  onCurrentFiresVisibleChange
}: SpotMapLayerSwitcherProps) => (
  <Paper
    elevation={3}
    sx={{
      position: 'absolute',
      top: 16,
      right: 16,
      zIndex: 2,
      p: 1.5,
      maxWidth: 260
    }}
  >
    <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'bold' }}>
      Layers
    </Typography>
    <FormGroup>
      <FormControlLabel
        control={
          <Checkbox
            size="small"
            checked={currentFiresVisible}
            onChange={event => onCurrentFiresVisibleChange(event.target.checked)}
          />
        }
        label={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 18,
                height: 12,
                border: '2px solid #B3261E',
                backgroundColor: 'rgba(179, 38, 30, 0.16)'
              }}
            />
            <Typography variant="body2">Current Fires</Typography>
          </Box>
        }
      />
    </FormGroup>
    <Typography variant="subtitle2" sx={{ mt: 1.5, mb: 1, fontWeight: 'bold' }}>
      Status
    </Typography>
    <FormGroup>
      <FormControlLabel
        control={
          <Checkbox
            size="small"
            checked={selectedStatuses.length === statusOptions.length}
            indeterminate={selectedStatuses.length > 0 && selectedStatuses.length < statusOptions.length}
            onChange={event => onAllStatusesChange(event.target.checked)}
          />
        }
        label="All"
      />
      {statusOptions.map(status => (
        <FormControlLabel
          key={status}
          sx={{ ml: 0.5 }}
          control={
            <Checkbox
              size="small"
              checked={selectedStatuses.includes(status)}
              onChange={event => onStatusChange(status, event.target.checked)}
            />
          }
          label={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                component="img"
                src={statusToPath[status]}
                alt=""
                sx={{ width: 18, height: 18, objectFit: 'contain' }}
              />
              <Typography variant="body2">{status}</Typography>
            </Box>
          }
        />
      ))}
    </FormGroup>
  </Paper>
)

export default SpotMapLayerSwitcher
