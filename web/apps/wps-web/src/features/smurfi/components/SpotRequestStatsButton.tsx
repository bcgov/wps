import AssessmentOutlinedIcon from '@mui/icons-material/AssessmentOutlined'
import { Box, Button, Chip, Divider, Popover, Stack, Typography } from '@mui/material'
import { SpotRequestStatusColorMap } from '@/features/smurfi/interfaces'
import { SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { useMemo, useState } from 'react'

interface SpotRequestStatsButtonProps {
  spotRequests: SpotRequestOutput[]
}

interface ForecasterStats {
  name: string
  active: number
  total: number
}

const STATUS_ORDER = [
  SpotRequestStatus.REQUESTED,
  SpotRequestStatus.STARTED,
  SpotRequestStatus.SUSPENDED,
  SpotRequestStatus.COMPLETE,
  SpotRequestStatus.ARCHIVED
]

const NO_FORECAST_LABEL = 'No forecast yet'

const SpotRequestStatsButton = ({ spotRequests }: SpotRequestStatsButtonProps) => {
  const [anchorEl, setAnchorEl] = useState<HTMLButtonElement | null>(null)
  const open = Boolean(anchorEl)

  const statusCounts = useMemo(
    () =>
      STATUS_ORDER.map(status => ({
        status,
        count: spotRequests.filter(spotRequest => spotRequest.status === status).length
      })),
    [spotRequests]
  )

  const forecasterStats = useMemo(() => {
    const statsByName = spotRequests.reduce<Record<string, ForecasterStats>>((stats, spotRequest) => {
      const name = spotRequest.latest_forecast?.forecaster_name ?? NO_FORECAST_LABEL
      const existing = stats[name] ?? { name, active: 0, total: 0 }

      stats[name] = {
        ...existing,
        active: existing.active + (spotRequest.status === SpotRequestStatus.STARTED ? 1 : 0),
        total: existing.total + 1
      }
      return stats
    }, {})

    return Object.values(statsByName).sort(
      (a, b) => b.active - a.active || b.total - a.total || a.name.localeCompare(b.name)
    )
  }, [spotRequests])

  return (
    <>
      <Button
        variant="outlined"
        size="small"
        startIcon={<AssessmentOutlinedIcon />}
        onClick={event => setAnchorEl(event.currentTarget)}
        sx={{ height: 40, whiteSpace: 'nowrap' }}
      >
        Stats
      </Button>
      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Box sx={{ p: 2, width: 320 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Status
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {statusCounts.map(({ status, count }) => {
              const colors = SpotRequestStatusColorMap[status]
              return (
                <Chip
                  key={status}
                  label={`${status}: ${count}`}
                  size="small"
                  sx={{
                    bgcolor: colors.bgColor,
                    color: colors.color,
                    border: 1,
                    borderColor: colors.borderColor
                  }}
                />
              )
            })}
          </Box>
          <Divider sx={{ my: 2 }} />
          <Typography variant="h6" sx={{ mb: 1 }}>
            Forecasters
          </Typography>
          <Stack spacing={1}>
            {forecasterStats.map(({ name, active, total }) => (
              <Box key={name} sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
                <Typography variant="body2" noWrap title={name}>
                  {name}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
                  {name === NO_FORECAST_LABEL ? `${total} total` : `${active} active / ${total} total`}
                </Typography>
              </Box>
            ))}
          </Stack>
        </Box>
      </Popover>
    </>
  )
}

export default SpotRequestStatsButton
