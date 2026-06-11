import { Box, Typography, useTheme } from '@mui/material'
import AsaIcon from '@/assets/asa-go-transparent.png'
import AppDescription from '@/components/AppDescription'
import LoginActions from '@/components/LoginActions'
import { useIsXSSmallScreen } from '@/hooks/useIsXSScreen'

// Landscape orientation landing page for phones only, not to be used with tablets.
const LandscapeLandingPage = () => {
  const theme = useTheme()
  const isXSSmallScreen = useIsXSSmallScreen()

  return (
    <Box
      sx={{
        bgcolor: theme.palette.primary.dark,
        display: 'flex',
        height: '100vh'
      }}
    >
      <Box
        sx={{
          alignItems: 'center',
          display: 'flex',
          flexDirection: 'row',
          px: theme.spacing(2),
          width: '100%',
          paddingRight: 'env(safe-area-inset-right)',
          paddingLeft: 'env(safe-area-inset-left)'
        }}
      >
        <Box
          sx={{
            alignItems: 'center',
            display: 'flex',
            flex: '0 0 40%',
            flexDirection: 'column',
            justifyContent: 'center'
          }}
        >
          <Box
            component="img"
            sx={{
              height: isXSSmallScreen ? '200px' : '250px',
              width: isXSSmallScreen ? '200px' : '250px'
            }}
            src={AsaIcon}
          />
          <Typography sx={{ color: 'white', fontWeight: 'bold' }} variant="h3">
            ASA Go
          </Typography>
        </Box>
        <Box
          sx={{
            alignItems: 'center',
            display: 'flex',
            flex: 1,
            flexDirection: 'column',
            pl: theme.spacing(2)
          }}
        >
          <Box sx={{ maxWidth: '80%' }}>
            <AppDescription />
          </Box>
          <Box
            sx={{
              alignItems: 'center',
              display: 'flex',
              justifyContent: 'center',
              pt: theme.spacing(4)
            }}
          >
            <LoginActions direction="row" />
          </Box>
        </Box>
      </Box>
    </Box>
  )
}

export default LandscapeLandingPage
