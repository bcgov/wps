import { useState } from 'react'
import { SpotAdminRow, SpotForecastStatusColorMap, SpotForecastStatus } from '@/features/smurfi/interfaces'
import { Card, CardContent, Typography, Button, Grid, Box, Link } from '@mui/material'
import DescriptionIcon from '@mui/icons-material/Description'
import { DateTime } from 'luxon'
import { getSpotPDF } from '@/api/SMURFIAPI'

interface SpotRequestCardProps {
  spot: SpotAdminRow
}

const SpotRequestCard = ({ spot }: SpotRequestCardProps) => {
  const handleViewPDF = async () => {
    try {
      const pdfBlob = await getSpotPDF(spot.id)
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
          <Grid item xs={6}>
            <Typography variant="body2" fontWeight="bold">
              {spot.fire_id}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Grid container spacing={1}>
              <Grid item xs={6}>
                <Button
                  variant="outlined"
                  color="primary"
                  sx={{ backgroundColor: '#e3f2fd', height: '36.5px', width: '100%' }}
                >
                  Subscribe
                </Button>
              </Grid>
              <Grid item xs={6}>
                <Box
                  sx={{
                    backgroundColor: SpotForecastStatusColorMap[spot.status].bgColor,
                    borderRadius: '4px',
                    alignItems: 'center',
                    justifyContent: 'center',
                    display: 'flex',
                    height: '36.5px',
                    width: '100%',
                    borderWidth: 1,
                    borderStyle: 'solid',
                    borderColor: SpotForecastStatusColorMap[spot.status].borderColor
                  }}
                >
                  <Typography variant="body2" sx={{ color: SpotForecastStatusColorMap[spot.status].color }}>
                    {spot.status}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" fontWeight="bold">
              {spot.fire_centre}
            </Typography>
          </Grid>
          <Grid item xs={6} style={{ textAlign: 'right' }}>
            <Link href="#" variant="body2">
              <Box display="flex" justifyContent="flex-end">
                <Typography variant="body2" style={{ marginRight: 4 }}>
                  {spot.latitude},
                </Typography>
                <Typography variant="body2">{spot.longitude}</Typography>
              </Box>
            </Link>
          </Grid>
        </Grid>
        <Box display="flex" justifyContent="center" mt={3}>
          <Button variant="outlined" startIcon={<DescriptionIcon />} sx={{ width: '100%' }} onClick={handleViewPDF}>
            {spot.status === SpotForecastStatus.NEW
              ? 'New Spot Forecast'
              : spot.last_updated
                ? `Latest Spot Forecast - ${DateTime.fromMillis(spot.last_updated).toFormat('dd/MM/yy - HH:mm')}`
                : 'Latest Spot Forecast'}
          </Button>
        </Box>
        <Box display="flex" justifyContent="center" mt={2}>
          <Link href="#" variant="body2">
            VIEW MORE
          </Link>
        </Box>
      </CardContent>
    </Card>
  )
}

export default SpotRequestCard
