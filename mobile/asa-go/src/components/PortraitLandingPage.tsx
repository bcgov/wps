import { Box, Typography, type TypographyVariant, useTheme } from '@mui/material'
import AsaIcon from '@/assets/asa-go-transparent.png'
import AppDescription from '@/components/AppDescription'
import LoginActions from '@/components/LoginActions'
import { useIsTablet } from '@/hooks/useIsTablet'
import { useIsXSSmallScreen } from '@/hooks/useIsXSScreen'

const PortraitLandingPage = () => {
  const theme = useTheme()
  const isXSSmallScreen = useIsXSSmallScreen()
  const isTablet = useIsTablet()

  const getValueByScreenSize = (xs: string, sm: string, md: string) => {
    if (isXSSmallScreen) {
      return xs
    }
    if (isTablet) {
      return md
    }
    return sm
  }

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
          flexDirection: 'column',
          justifyContent: 'center',
          paddingTop: 'env(safe-area-inset-top)',
          paddingBottom: 'env(safe-area-inset-bottom)',
          width: '100%'
        }}
      >
        <Box
          component="img"
          sx={{
            height: getValueByScreenSize('200px', '300px', '350px'),
            width: getValueByScreenSize('200px', '300px', '350px')
          }}
          src={AsaIcon}
        />
        <Box
          sx={{
            alignItems: 'center',
            justifyContent: 'center',
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          <Typography
            sx={{
              color: 'white',
              fontWeight: 'bold',
              mb: theme.spacing(2)
            }}
            variant={getValueByScreenSize('h4', 'h3', 'h2') as TypographyVariant}
          >
            ASA Go
          </Typography>
        </Box>
        <Box
          sx={{
            maxWidth: getValueByScreenSize('100%', '80%', '50%'),
            width: '100%'
          }}
        >
          <AppDescription />
          <Box
            sx={{
              alignItems: 'center',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              pt: theme.spacing(4),
              width: '100%'
            }}
          >
            <LoginActions />
          </Box>
        </Box>
      </Box>
      );
    </Box>
  )
}

export default PortraitLandingPage
