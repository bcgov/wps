import SpotRequestForm from '@/features/smurfi/components/requestForm/SpotRequestForm'
import { Box, Button, Typography } from '@mui/material'
import { SpotRequestOutput } from '@wps/api/SMURFIAPI'
import { getSmurfiRequestRoute, SMURFI_DASHBOARD_ROUTE } from '@wps/utils/constants'
import { useNavigate, useLocation } from 'react-router-dom'

interface NewRequestLocationState {
  latitude?: number
  longitude?: number
}

const SpotRequestFormPage = () => {
  const navigate = useNavigate()
  const { state } = useLocation()
  const locationState = (state as NewRequestLocationState | null) ?? {}
  const initialLocation =
    locationState.latitude != null && locationState.longitude != null
      ? { latitude: locationState.latitude, longitude: locationState.longitude }
      : undefined

  const handleSubmit = (spotRequest: SpotRequestOutput) => {
    navigate(getSmurfiRequestRoute(spotRequest.id))
  }

  return (
    <Box sx={{ width: '100%', maxWidth: 1440, mx: 'auto', pb: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Request a Spot Forecast</Typography>
        <Button variant="outlined" onClick={() => navigate(SMURFI_DASHBOARD_ROUTE)}>
          Back to Dashboard
        </Button>
      </Box>
      <SpotRequestForm
        onCancel={() => navigate(SMURFI_DASHBOARD_ROUTE)}
        onSubmit={handleSubmit}
        initialLocation={initialLocation}
      />
    </Box>
  )
}

export default SpotRequestFormPage
