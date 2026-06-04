import { AppDispatch } from '@/app/store'
import { statusToPath } from '@/features/smurfi/components/map/SpotStatusMarkers'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import { SpotRequestStatusColorMap } from '@/features/smurfi/interfaces'
import { updateSpotRequestStatus } from '@/features/smurfi/slices/smurfiSlice'
import { canChangeSpotStatus, getAllowedSpotStatusOptions } from '@/features/smurfi/utils/spotStatusUtils'
import ArrowDropDownIcon from '@mui/icons-material/ArrowDropDown'
import { Box, Button, Menu, MenuItem, Typography } from '@mui/material'
import { SpotRequestOutput, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { MouseEvent, useState } from 'react'
import { useDispatch } from 'react-redux'

interface SpotStatusControlProps {
  spotRequest: SpotRequestOutput
  fullWidth?: boolean
  onStatusChanged?: (spotRequest: SpotRequestOutput) => void
}

const StatusContent = ({ status }: { status: SpotRequestStatus }) => (
  <>
    <Box component="img" src={statusToPath[status]} alt="" sx={{ width: 14, height: 18, objectFit: 'contain' }} />
    <Typography variant="body2" component="span" sx={{ fontWeight: 500 }}>
      {status}
    </Typography>
  </>
)

const getStatusSx = (status: SpotRequestStatus, fullWidth: boolean) => {
  const colors = SpotRequestStatusColorMap[status]
  return {
    backgroundColor: colors.bgColor,
    border: `1px solid ${colors.borderColor}`,
    borderRadius: 1,
    color: colors.color,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 0.75,
    minHeight: 30,
    minWidth: fullWidth ? '100%' : 116,
    width: fullWidth ? '100%' : 'auto',
    px: 1,
    textTransform: 'none',
    '&:hover': {
      backgroundColor: colors.bgColor,
      borderColor: colors.borderColor
    },
    '&.Mui-disabled': {
      color: colors.color,
      opacity: 0.8
    }
  }
}

const SpotStatusControl = ({ spotRequest, fullWidth = false, onStatusChanged }: SpotStatusControlProps) => {
  const dispatch = useDispatch<AppDispatch>()
  const { isOwner, isForecaster } = useSpotPermissions(spotRequest)
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null)
  const [isUpdating, setIsUpdating] = useState(false)
  const allowedStatuses = getAllowedSpotStatusOptions({ spotRequest, isOwner, isForecaster })
  const isEditable = canChangeSpotStatus({ spotRequest, isOwner, isForecaster })
  const open = Boolean(anchorEl)

  const handleOpen = (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleStatusChange = async (status: SpotRequestStatus) => {
    handleClose()
    if (status === spotRequest.status) {
      return
    }

    setIsUpdating(true)
    const result = await dispatch(updateSpotRequestStatus({ spotRequestId: spotRequest.id, status }))
    setIsUpdating(false)

    if (!result.spotRequest) {
      return
    }

    onStatusChanged?.(result.spotRequest)
  }

  if (!isEditable) {
    return (
      <Box sx={getStatusSx(spotRequest.status, fullWidth)}>
        <StatusContent status={spotRequest.status} />
      </Box>
    )
  }

  return (
    <>
      <Button
        size="small"
        endIcon={<ArrowDropDownIcon />}
        disabled={isUpdating}
        onClick={handleOpen}
        sx={getStatusSx(spotRequest.status, fullWidth)}
      >
        <StatusContent status={spotRequest.status} />
      </Button>
      <Menu anchorEl={anchorEl} open={open} onClose={handleClose}>
        {allowedStatuses.map(status => (
          <MenuItem key={status} selected={status === spotRequest.status} onClick={() => handleStatusChange(status)}>
            {status}
          </MenuItem>
        ))}
      </Menu>
    </>
  )
}

export default SpotStatusControl
