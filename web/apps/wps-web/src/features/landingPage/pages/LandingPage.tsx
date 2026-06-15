import { Box } from '@mui/material'
import { useTheme } from '@mui/material/styles'
import useMediaQuery from '@mui/material/useMediaQuery'
import { LANDING_BACKGROUND_COLOUR } from '@wps/ui/theme'
import { LANDING_PAGE_DOC_TITLE } from '@wps/utils/constants'
import Footer from 'features/landingPage/components/Footer'
import Sidebar from 'features/landingPage/components/Sidebar'
import ToolCards from 'features/landingPage/components/ToolCards'
import type React from 'react'
import { useEffect } from 'react'

const LandingPage: React.FunctionComponent = () => {
  const theme = useTheme()
  const isSmall = useMediaQuery(theme.breakpoints.down('sm'))

  useEffect(() => {
    document.title = LANDING_PAGE_DOC_TITLE
  }, [])

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        maxHeight: '100vh',
        minHeight: '100vh',
        overflow: 'hidden'
      }}
    >
      <Box sx={{ display: 'flex', flexDirection: 'row', flexGrow: 1, overflow: 'hidden' }}>
        <Box
          sx={{
            display: 'flex',
            overflowY: 'auto',
            [theme.breakpoints.up('sm')]: {
              minWidth: '265px',
              maxWidth: '265px',
              width: '265px'
            }
          }}
        >
          <Sidebar />
        </Box>
        <Box sx={{ bgcolor: LANDING_BACKGROUND_COLOUR, display: 'flex', flexGrow: 1, overflowY: 'auto' }}>
          {!isSmall && <ToolCards />}
        </Box>
      </Box>
      <Footer />
    </Box>
  )
}

export default LandingPage
