import { selectFireCentres } from '@/app/rootReducer'
import { SpotRequestStatusColorMap } from '@/features/smurfi/interfaces'
import { selectSmurfi } from '@/features/smurfi/slices/smurfiSlice'
import SmurfiRequestsMap from '@/features/smurfi/components/map/SmurfiRequestsMap'
import GroupsIcon from '@mui/icons-material/Groups'
import { Box, Button, Chip, Divider, Paper, Typography } from '@mui/material'
import { SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { DateTime } from 'luxon'
import { selectSubscribedIds, toggleSpotSubscription } from '@/features/smurfi/slices/subscriptionsSlice'
import useSpotPermissions from '@/features/smurfi/hooks/useSpotPermissions'
import { AppDispatch } from '@/app/store'
import { useDispatch, useSelector } from 'react-redux'
import { useNavigate, useParams } from 'react-router-dom'
import { SMURFI_DASHBOARD_ROUTE } from '@wps/utils/constants'

const Field = ({ label, value }: { label: string; value: React.ReactNode }) => (
  <Box>
    <Typography
      variant="caption"
      color="text.secondary"
      sx={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.8 }}
    >
      {label}
    </Typography>
    <Typography variant="body1">{value}</Typography>
  </Box>
)

const Section = ({
  title,
  children,
  sx,
  contentSx,
  action
}: {
  title: string
  children: React.ReactNode
  sx?: object
  contentSx?: object
  action?: React.ReactNode
}) => (
  <Paper variant="outlined" sx={{ p: 2.5, display: 'flex', flexDirection: 'column', ...sx }}>
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 600, letterSpacing: 1.5 }}>
        {title}
      </Typography>
      {action}
    </Box>
    <Divider sx={{ mt: 0.5, mb: 2 }} />
    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, flex: 1, ...contentSx }}>{children}</Box>
  </Paper>
)

const formatDate = (iso: string) => {
  const dt = DateTime.fromISO(iso)
  return dt.isValid ? dt.toFormat('MMM d, yyyy') : iso
}

const SpotRequest = () => {
  const dispatch: AppDispatch = useDispatch()
  const { id } = useParams()
  const navigate = useNavigate()
  const { spotRequests } = useSelector(selectSmurfi)
  const { fireCentres } = useSelector(selectFireCentres)
  const subscribedIds = useSelector(selectSubscribedIds)

  const spotRequest = spotRequests.find(sr => sr.id === Number(id))
  const { isOwner, isForecaster } = useSpotPermissions(spotRequest)

  if (!spotRequest) {
    return (
      <Typography variant="body1" color="text.secondary">
        Spot request not found.
      </Typography>
    )
  }

  const isSubscribed = subscribedIds.includes(spotRequest.id)

  const fireCentreName =
    fireCentres.find(fc => fc.id === spotRequest.fire_centre)?.name?.replace(/ Fire Centre$/, '') ??
    String(spotRequest.fire_centre)

  const statusColors = SpotRequestStatusColorMap[spotRequest.status as SpotRequestStatus]
  const requestInstance = spotRequest.initial_instance

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2, alignItems: 'stretch' }}>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Section
          title="Request Details"
          action={
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button variant="outlined" size="small" onClick={() => dispatch(toggleSpotSubscription(spotRequest.id))}>
                {isSubscribed ? 'Unsubscribe' : 'Subscribe'}
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate(`${SMURFI_DASHBOARD_ROUTE}/${spotRequest.id}/forecasts`)}
              >
                View Forecasts
              </Button>
              {(isOwner || isForecaster) && (
                <Button variant="outlined" size="small" onClick={() => console.log(spotRequest.requestor_idir)}>
                  Edit Request
                </Button>
              )}
            </Box>
          }
        >
          <Box>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.8, display: 'block' }}
            >
              Status
            </Typography>
            <Box
              sx={{
                display: 'inline-flex',
                alignItems: 'center',
                backgroundColor: statusColors?.bgColor,
                borderRadius: '4px',
                px: 1.5,
                py: 0.25,
                border: 1,
                borderColor: statusColors?.borderColor,
                mt: 0.25
              }}
            >
              <Typography variant="body2" sx={{ color: statusColors?.color, fontWeight: 500 }}>
                {spotRequest.status}
              </Typography>
            </Box>
          </Box>
          <Box>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.8, display: 'block' }}
            >
              Fire Number(s)
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
              {spotRequest.fire_number.map(fn => (
                <Chip key={fn} label={fn} size="small" />
              ))}
            </Box>
          </Box>
          <Field label="Fire Centre" value={fireCentreName} />
          <Field label="Forecast Type" value={spotRequest.request_type} />
          <Field label="Start Date" value={formatDate(spotRequest.start_at)} />
          <Field label="End Date" value={formatDate(spotRequest.end_at)} />
          <Box>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.8, display: 'block' }}
            >
              Requested Frequency
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, max-content)', gap: 0.5, mt: 0.5 }}>
              {spotRequest.request_frequency.map(day => (
                <Chip key={day} label={day} size="small" />
              ))}
            </Box>
          </Box>
          <Field label="Geographic Description" value={requestInstance.geographic_description} />
          <Field label="Elevation" value={requestInstance.elevation ? `${requestInstance.elevation} m` : '—'} />
          <Field label="Slope / Aspect" value={requestInstance.aspect ?? '—'} />
          {spotRequest.additional_information && (
            <Field label="Additional Info" value={spotRequest.additional_information} />
          )}
          {spotRequest.subscribers.length > 0 && (
            <Box>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.8, display: 'block' }}
              >
                Subscribers
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                {spotRequest.subscribers.map(sub => (
                  <Chip key={sub.email} label={sub.email} size="small" />
                ))}
              </Box>
            </Box>
          )}
          {spotRequest.distribution_groups && spotRequest.distribution_groups.length > 0 && (
            <Box>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.8, display: 'block' }}
              >
                Distribution Groups
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                {spotRequest.distribution_groups.map(group => (
                  <Chip key={group.id} label={group.name} icon={<GroupsIcon />} size="small" color="primary" variant="outlined" />
                ))}
              </Box>
            </Box>
          )}
        </Section>
        <Section title="Requestor Details">
          <Field label="Requestor Name" value={spotRequest.requestor_name} />
          <Field label="Requestor IDIR" value={spotRequest.requestor_idir} />
          <Field label="Requestor Email" value={spotRequest.requestor_email} />
          <Field label="Requested At" value={formatDate(spotRequest.requested_at)} />
        </Section>
      </Box>

      <Section title="Location" sx={{ height: '100%' }} contentSx={{ gridTemplateRows: 'auto 1fr' }}>
        <Field label="Latitude" value={Number(requestInstance.latitude).toFixed(4)} />
        <Field label="Longitude" value={Number(requestInstance.longitude).toFixed(4)} />
        <Box sx={{ gridColumn: '1 / -1', minHeight: 0, border: '1px solid black' }}>
          <SmurfiRequestsMap spotRequest={spotRequest} spotRequestInstance={requestInstance} />
        </Box>
      </Section>
    </Box>
  )
}

export default SpotRequest
