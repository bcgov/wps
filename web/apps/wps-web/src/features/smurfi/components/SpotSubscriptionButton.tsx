import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive'
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone'
import { Button, ButtonProps, Tooltip } from '@mui/material'
import { AppDispatch } from '@/app/store'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import {
  selectSubscribedIds,
  selectSubscriptionsLoading,
  toggleSpotSubscription
} from '@/features/smurfi/slices/subscriptionsSlice'
import { SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { useDispatch, useSelector } from 'react-redux'

interface SpotSubscriptionButtonProps {
  spotRequest: SpotRequestOutput
  size?: ButtonProps['size']
  variant?: ButtonProps['variant']
  color?: ButtonProps['color']
  fullWidth?: boolean
}

const OWNER_TOOLTIP = 'The owner of a spot request cannot unsubscribe from forecast notifications.'

const SpotSubscriptionButton = ({
  spotRequest,
  size = 'small',
  variant = 'outlined',
  color = 'primary',
  fullWidth = false
}: SpotSubscriptionButtonProps) => {
  const dispatch = useDispatch<AppDispatch>()
  const subscribedIds = useSelector(selectSubscribedIds)
  const isLoading = useSelector(selectSubscriptionsLoading)
  const { isOwner } = useSpotPermissions(spotRequest)
  const isSubscribed = isOwner || subscribedIds.includes(spotRequest.id)
  const label = isOwner ? 'Subscribed' : isSubscribed ? 'Unsubscribe' : 'Subscribe'
  const startIcon = isSubscribed ? <NotificationsActiveIcon /> : <NotificationsNoneIcon />

  const button = (
    <Button
      startIcon={startIcon}
      size={size}
      variant={variant}
      color={color}
      fullWidth={fullWidth}
      disabled={isOwner || isLoading}
      onClick={() => dispatch(toggleSpotSubscription(spotRequest.id))}
    >
      {label}
    </Button>
  )

  if (!isOwner) {
    return button
  }

  return (
    <Tooltip title={OWNER_TOOLTIP}>
      <span style={{ display: fullWidth ? 'block' : 'inline-flex', width: fullWidth ? '100%' : undefined }}>
        {button}
      </span>
    </Tooltip>
  )
}

export default SpotSubscriptionButton
