import LockOutlinedIcon from '@mui/icons-material/LockOutlined'
import PublicOutlinedIcon from '@mui/icons-material/PublicOutlined'
import StarIcon from '@mui/icons-material/Star'
import Box from '@mui/material/Box'
import Container from '@mui/material/Container'
import Stack from '@mui/material/Stack'
import Footer from 'features/landingPage/components/Footer'
import { useEffect, useState } from 'react'
import { readFavouriteRoutes, storeFavouriteRoutes } from '@/features/landingPage/LandingPagePreview/favouritesStorage'
import LandingPageHeader from './LandingPageHeader'
import {
  BCWS_SECTION_ID,
  bcwsTools,
  FAVOURITES_SECTION_ID,
  LANDING_PAGE_FAVOURITES_STORAGE_KEY,
  landingPagePreviewTools,
  PUBLIC_SECTION_ID,
  publicTools
} from './landingPagePreviewConfig'
import QuickAccessDrawer from './QuickAccessDrawer'
import ToolSection from './ToolSection'

export { LANDING_PAGE_FAVOURITES_STORAGE_KEY }

const LandingPagePreview = () => {
  const [favouriteRoutes, setFavouriteRoutes] = useState<string[]>(readFavouriteRoutes)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const favouriteTools = landingPagePreviewTools.filter(tool => favouriteRoutes.includes(tool.route))
  const visibleBcwsTools = bcwsTools.filter(tool => !favouriteRoutes.includes(tool.route))
  const visiblePublicTools = publicTools.filter(tool => !favouriteRoutes.includes(tool.route))

  useEffect(() => {
    document.title = 'Landing Page Preview | BC Wildfire Service'
  }, [])

  useEffect(() => {
    storeFavouriteRoutes(favouriteRoutes)
  }, [favouriteRoutes])

  const toggleFavourite = (route: string) => {
    setFavouriteRoutes(current =>
      current.includes(route) ? current.filter(favouriteRoute => favouriteRoute !== route) : [...current, route]
    )
  }

  return (
    <Box sx={{ bgcolor: 'grey.50', display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <QuickAccessDrawer
        bcwsTools={visibleBcwsTools}
        favouriteRoutes={favouriteRoutes}
        favouriteTools={favouriteTools}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        onToggleFavourite={toggleFavourite}
        publicTools={visiblePublicTools}
      />

      <Container component="main" sx={{ flex: 1, py: { xs: 3, sm: 5 }, maxWidth: { xs: '100%', md: '75%', xl: 1200 } }}>
        <LandingPageHeader onOpenQuickAccess={() => setIsDrawerOpen(true)} />

        <Stack spacing={5}>
          {favouriteTools.length > 0 && (
            <ToolSection
              backgroundColor="#eef3ee"
              headingId={FAVOURITES_SECTION_ID}
              icon={<StarIcon sx={{ color: 'warning.main', fontSize: 18 }} />}
              isFavourite={route => favouriteRoutes.includes(route)}
              onToggleFavourite={toggleFavourite}
              title="My Favourites"
              tools={favouriteTools}
            />
          )}
          {visibleBcwsTools.length > 0 && (
            <ToolSection
              backgroundColor="#d9e8f5"
              headingId={BCWS_SECTION_ID}
              icon={<LockOutlinedIcon sx={{ fontSize: 18 }} />}
              isFavourite={route => favouriteRoutes.includes(route)}
              onToggleFavourite={toggleFavourite}
              title="BCWS Access Only"
              tools={visibleBcwsTools}
            />
          )}
          {visiblePublicTools.length > 0 && (
            <ToolSection
              backgroundColor="#fff4e5"
              headingId={PUBLIC_SECTION_ID}
              icon={<PublicOutlinedIcon sx={{ color: 'success.main', fontSize: 18 }} />}
              isFavourite={route => favouriteRoutes.includes(route)}
              onToggleFavourite={toggleFavourite}
              title="Public Access"
              tools={visiblePublicTools}
            />
          )}
        </Stack>
      </Container>
      <Footer />
    </Box>
  )
}

export default LandingPagePreview
