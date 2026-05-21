import { Card, CardContent, Typography, Button, Grid, Box, Link } from '@mui/material'
import DescriptionIcon from '@mui/icons-material/Description'
import { DateTime } from 'luxon'
import { useSelector, useDispatch } from 'react-redux'
import {
  selectSubscribedIds,
  selectSubscriptionsLoading,
  toggleSpotSubscription
} from '@/features/smurfi/slices/subscriptionsSlice'
import { AppDispatch } from 'app/store'
import { getSpotPDF, SpotAdminRow, SpotRequestStatus } from '@wps/api/SMURFIAPI'
import { SpotRequestStatusColorMap } from '@/features/smurfi/interfaces'

interface SpotRequestCardProps {
  spot: SpotAdminRow
  isAuthenticated: boolean
}

const SpotRequestCard = ({ spot, isAuthenticated }: SpotRequestCardProps) => {
  const dispatch = useDispatch<AppDispatch>()
  const subscribedIds = useSelector(selectSubscribedIds)
  const isSubscribed = subscribedIds.includes(spot.spot_id)
  const isLoading = useSelector(selectSubscriptionsLoading)

  const handleToggleSubscription = () => {
    dispatch(toggleSpotSubscription(spot.spot_id))
  }

  const handleViewPDF = async () => {
    try {
      const pdfBlob = await getSpotPDF(spot.spot_id)
      const url = URL.createObjectURL(pdfBlob)
      // Open PDF in new tab instead of modal for better compatibility
      window.open(url, '_blank')
    } catch (error) {
      console.error('Failed to load PDF:', error)
      // You might want to show an error message to the user here
    }
  }

  return (
    <Card sx={{ width: '400px', border: '1px solid lightgrey' }}>
      <CardContent>
        <Grid container spacing={2}>
          <Grid size={6}>
            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
              {spot.fire_id}
            </Typography>
          </Grid>
          <Grid size={6}>
            <Grid container spacing={1}>
              <Grid size={6}>
                <Button
                  variant="outlined"
                  color="primary"
                  disabled={isLoading}
                  sx={{ backgroundColor: '#e3f2fd', height: '36.5px', width: '100%' }}
                  onClick={handleToggleSubscription}
                >
                  {isSubscribed ? 'Unsubscribe' : 'Subscribe'}
                </Button>
              </Grid>
              <Grid size={6}>
                <Box
                  sx={{
                    backgroundColor: SpotRequestStatusColorMap[spot.status].bgColor,
                    borderRadius: '4px',
                    alignItems: 'center',
                    justifyContent: 'center',
                    display: 'flex',
                    height: '36.5px',
                    width: '100%',
                    borderWidth: 1,
                    borderStyle: 'solid',
                    borderColor: SpotRequestStatusColorMap[spot.status].borderColor
                  }}
                >
                  <Typography variant="body2" sx={{ color: SpotRequestStatusColorMap[spot.status].color }}>
                    {spot.status}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Grid>
          <Grid size={6}>
            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
              {spot.fire_centre}
            </Typography>
          </Grid>
          <Grid size={6} style={{ textAlign: 'right' }}>
            <Link href="#" variant="body2">
              <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Typography variant="body2" style={{ marginRight: 4 }}>
                  {spot.latitude},
                </Typography>
                <Typography variant="body2">{spot.longitude}</Typography>
              </Box>
            </Link>
          </Grid>
        </Grid>
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Button variant="outlined" startIcon={<DescriptionIcon />} sx={{ width: '100%' }} onClick={handleViewPDF}>
            {spot.status === SpotRequestStatus.REQUESTED
              ? 'New Spot Forecast'
              : spot.last_updated
                ? `Latest Spot Forecast - ${DateTime.fromMillis(spot.last_updated).toFormat('dd/MM/yy - HH:mm')}`
                : 'Latest Spot Forecast'}
          </Button>
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
          <Link href="#" variant="body2">
            VIEW MORE
          </Link>
        </Box>
      </CardContent>
    </Card>
  )
}

export default SpotRequestCard
