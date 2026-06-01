import { useSelector } from 'react-redux'
import { useNavigate, useParams } from 'react-router-dom'
import { selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import { Alert, Box, Button, CircularProgress, Typography } from '@mui/material'
import { DateTime } from 'luxon'
import SpotRequestForm from '@/features/smurfi/components/requestForm/SpotRequestForm'
import { getSmurfiRequestRoute } from '@wps/utils/constants'
import { SpotRequestFormValues } from '@wps/api/schema/spotRequestSchema'

const EditSpotRequestPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { spotRequests, spotRequestsLoading, spotRequestsError } = useSelector(selectSmurfi)

  const spotRequestId = Number(id)
  const requestRoute = getSmurfiRequestRoute(spotRequestId)

  const spotRequest = spotRequests.find(sr => sr.id === spotRequestId)
  const { isOwner, isForecaster } = useSpotPermissions(spotRequest)

  if (spotRequestsLoading) {
    return <CircularProgress aria-label="Loading spot request" />
  }

  if (spotRequestsError) {
    return <Alert severity="error">Unable to load spot request.</Alert>
  }

  if (!Number.isFinite(spotRequestId) || !spotRequest) {
    return <Alert severity="warning">Spot request not found.</Alert>
  }

  if (!isOwner && !isForecaster) {
    return <Alert severity="warning">You do not have permission to edit this request.</Alert>
  }

  const requestInstance = spotRequest.request_instance

  const editRequestValues: Partial<SpotRequestFormValues> = {
    fireNumbers: spotRequest.fire_number,
    fireCentreId: spotRequest.fire_centre,
    forecastStartDate: DateTime.fromISO(spotRequest.start_at).setZone('America/Vancouver'),
    forecastEndDate: DateTime.fromISO(spotRequest.end_at).setZone('America/Vancouver'),
    forecastType: spotRequest.request_type as SpotRequestFormValues['forecastType'],
    emailDistributionList: spotRequest.subscribers.filter(s => s.subscriber_status === 'active').map(s => s.email),
    distributionGroupIds: spotRequest.distribution_group_ids ?? [],
    requestedFrequency: spotRequest.request_frequency as SpotRequestFormValues['requestedFrequency'],
    location: {
      latitude: requestInstance.latitude,
      longitude: requestInstance.longitude
    },
    geographicDescription: requestInstance.geographic_description,
    slopeAspect: requestInstance.aspect ?? '',
    elevation: requestInstance.elevation != null ? String(requestInstance.elevation) : '',
    additionalInformation: spotRequest.additional_information ?? ''
  }

  return (
    <Box sx={{ width: '100%', maxWidth: 1440, mx: 'auto', pb: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Edit Spot Request</Typography>
        <Button variant="outlined" onClick={() => navigate(requestRoute)}>
          Back to Request
        </Button>
      </Box>
      <SpotRequestForm
        onCancel={() => navigate(requestRoute)}
        onSubmit={() => navigate(requestRoute)}
        editRequestValues={editRequestValues}
        spotRequestId={spotRequestId}
      />
    </Box>
  )
}

export default EditSpotRequestPage
