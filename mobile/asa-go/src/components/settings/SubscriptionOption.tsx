import { ListItem, ListItemButton, ListItemText, Typography } from '@mui/material'
import { useSelector } from 'react-redux'
import type { FireZoneUnit } from '@/api/fbaAPI'
import LoadingSwitch from '@/components/LoadingSwitch'
import { selectSettings } from '@/store'
import { fireZoneUnitNameFormatter } from '@/utils/stringUtils'

interface SubscriptionOptionProps {
  fireZoneUnit: FireZoneUnit
  onToggle: (fireZoneUnitId: number) => void
  disabled: boolean
  loading?: boolean
}

const SubscriptionOption = ({ fireZoneUnit, onToggle, disabled, loading }: SubscriptionOptionProps) => {
  const { subscriptions } = useSelector(selectSettings)
  const handleSwitchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.stopPropagation()
    onToggle(fireZoneUnit.id)
  }

  const handleSubscriptionUpdate = () => {
    onToggle(fireZoneUnit.id)
  }

  return (
    <ListItem disableGutters disablePadding>
      <ListItemButton disableRipple onClick={handleSubscriptionUpdate}>
        <ListItemText>
          <Typography
            variant="body2"
            sx={{
              fontWeight: 'bold',
              whiteSpace: 'pre-line'
            }}
          >
            {fireZoneUnitNameFormatter(fireZoneUnit.name)}
          </Typography>
        </ListItemText>
        {/* biome-ignore lint/a11y/noStaticElementInteractions: click handler only stops propagation so the switch doesn't trigger the surrounding ListItemButton */}
        {/* biome-ignore lint/a11y/useKeyWithClickEvents: propagation guard is mouse-only; the switch itself stays keyboard accessible */}
        <span onClick={e => e.stopPropagation()}>
          <LoadingSwitch
            edge="end"
            disabled={disabled}
            loading={loading}
            checked={subscriptions.includes(fireZoneUnit.id)}
            onChange={handleSwitchChange}
            aria-label={`Toggle subscription for ${fireZoneUnit.name}`}
          />
        </span>
      </ListItemButton>
    </ListItem>
  )
}

export default SubscriptionOption
