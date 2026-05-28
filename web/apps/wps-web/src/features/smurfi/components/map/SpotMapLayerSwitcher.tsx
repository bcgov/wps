import { Autocomplete, Box, Checkbox, FormControlLabel, FormGroup, Paper, TextField, Typography } from '@mui/material'
import { SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { statusToPath } from '@/features/smurfi/components/map/SpotStatusMarkers'
import { CURRENT_FIRE_STATUS_COLORS } from '@/features/smurfi/components/map/currentFirePolygonsLayer'
import { CURRENT_FIRE_STATUS_OPTIONS, CurrentFireStatus } from '@/features/smurfi/components/map/mapLayerVisibility'

interface SpotMapLayerSwitcherProps {
  statusOptions: SpotRequestStatus[]
  selectedStatuses: SpotRequestStatus[]
  currentFiresVisible: boolean
  selectedCurrentFireStatuses: CurrentFireStatus[]
  allFireNumbers?: string[]
  selectedFireNumbers?: string[]
  onStatusChange: (status: SpotRequestStatus, checked: boolean) => void
  onAllStatusesChange: (checked: boolean) => void
  onCurrentFiresVisibleChange: (checked: boolean) => void
  onCurrentFireStatusChange: (status: CurrentFireStatus, checked: boolean) => void
  onFireNumbersChange?: (fireNumbers: string[]) => void
}

const SpotMapLayerSwitcher = ({
  statusOptions,
  selectedStatuses,
  currentFiresVisible,
  selectedCurrentFireStatuses,
  allFireNumbers,
  selectedFireNumbers,
  onStatusChange,
  onAllStatusesChange,
  onCurrentFiresVisibleChange,
  onCurrentFireStatusChange,
  onFireNumbersChange
}: SpotMapLayerSwitcherProps) => (
  <Paper
    elevation={3}
    sx={{
      position: 'absolute',
      top: 16,
      right: 16,
      zIndex: 2,
      p: 1.5,
      maxWidth: 260,
      minWidth: 200
    }}
  >
    {allFireNumbers && selectedFireNumbers && onFireNumbersChange && (
      <>
        <Typography variant="subtitle2" sx={{ mb: 0.5, fontWeight: 'bold' }}>
          Fire Number
        </Typography>
        <Autocomplete
          multiple
          size="small"
          options={allFireNumbers}
          value={selectedFireNumbers}
          onChange={(_, value) => onFireNumbersChange(value)}
          renderInput={params => (
            <TextField {...params} placeholder={selectedFireNumbers.length === 0 ? 'All fires' : ''} />
          )}
          sx={{ mb: 1.5 }}
        />
      </>
    )}
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
      {currentFiresVisible &&
        CURRENT_FIRE_STATUS_OPTIONS.map(status => (
          <FormControlLabel
            key={status}
            sx={{ ml: 0.5 }}
            control={
              <Checkbox
                size="small"
                checked={selectedCurrentFireStatuses.includes(status)}
                onChange={event => onCurrentFireStatusChange(status, event.target.checked)}
              />
            }
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box
                  sx={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: CURRENT_FIRE_STATUS_COLORS[status],
                    border: '1px solid #FFFFFF',
                    boxShadow: '0 0 0 1px rgba(0, 0, 0, 0.35)'
                  }}
                />
                <Typography variant="body2">{status}</Typography>
              </Box>
            }
          />
        ))}
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
                sx={{ width: 18, height: 24, objectFit: 'contain' }}
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
