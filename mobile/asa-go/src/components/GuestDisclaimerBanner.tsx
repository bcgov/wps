import { Box, Typography, useTheme } from '@mui/material'
import { useSelector } from 'react-redux'
import InfoIcon from '@/assets/InfoIcon.svg'
import { selectAuthentication } from '@/store'

const GuestDisclaimerBanner = () => {
  const theme = useTheme()
  const { sessionMode } = useSelector(selectAuthentication)

  if (sessionMode !== 'guest') {
    return null
  }

  return (
    <Box
      component="span"
      data-testid="guest-disclaimer-banner"
      sx={{
        backgroundColor: theme.palette.info.main,
        color: 'black',
        padding: theme.spacing(0.5),
        display: 'inline-flex',
        alignItems: 'center',
        borderLeftColor: theme.palette.info.dark,
        borderLeftStyle: 'solid',
        borderLeftWidth: '4px'
      }}
    >
      <Box component="img" src={InfoIcon} sx={{ px: theme.spacing(1) }} />
      <Typography component="span" variant="body2">
        <Typography component="span" variant="body2" sx={{ fontWeight: 'bold' }}>
          Note:
        </Typography>
        {' '}These are not public safety warnings
      </Typography>
    </Box>
  )
}

export default GuestDisclaimerBanner
