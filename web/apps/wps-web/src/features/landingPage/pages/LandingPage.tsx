import LockOutlinedIcon from '@mui/icons-material/LockOutlined'
import PublicOutlinedIcon from '@mui/icons-material/PublicOutlined'
import StarIcon from '@mui/icons-material/Star'
import Box from '@mui/material/Box'
import Container from '@mui/material/Container'
import GlobalStyles from '@mui/material/GlobalStyles'
import Stack from '@mui/material/Stack'
import { PUBLIC_TOOL_ICON_COLOUR } from '@wps/ui/theme'
import { LANDING_PAGE_DOC_TITLE } from '@wps/utils/constants'
import Footer from 'features/landingPage/components/Footer'
import { useEffect, useState } from 'react'
import { readFavouriteRoutes, storeFavouriteRoutes } from '@/features/landingPage/favouritesStorage'
import LandingPageHeader from '../components/LandingPageHeader'
import QuickAccessDrawer from '../components/QuickAccessDrawer'
import ToolSection from '../components/ToolSection'
import { bcpsTools, landingPageTools, publicTools } from '../landingPageTools'

const BCPS_SECTION_ID = 'bcps-access-only-heading'
const FAVOURITES_COLOUR = '#3f743f'
const FAVOURITES_SECTION_ID = 'favourites-heading'
const PUBLIC_SECTION_ID = 'public-access-heading'

const LandingPage = () => {
  const [favouriteRoutes, setFavouriteRoutes] = useState<string[]>(readFavouriteRoutes)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const favouriteTools = landingPageTools.filter(tool => favouriteRoutes.includes(tool.route))
  const visibleBcpsTools = bcpsTools.filter(tool => !favouriteRoutes.includes(tool.route))
  const visiblePublicTools = publicTools.filter(tool => !favouriteRoutes.includes(tool.route))

  useEffect(() => {
    document.title = LANDING_PAGE_DOC_TITLE
  }, [])

  const toggleFavourite = (route: string) => {
    setFavouriteRoutes(current => {
      const next = current.includes(route)
        ? current.filter(favouriteRoute => favouriteRoute !== route)
        : [...current, route]
      storeFavouriteRoutes(next)
      return next
    })
  }

  return (
    <Box sx={{ bgcolor: 'grey.50', display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <GlobalStyles styles={{ html: { scrollbarGutter: 'stable' } }} />
      <QuickAccessDrawer
        bcpsTools={visibleBcpsTools}
        favouritesColour={FAVOURITES_COLOUR}
        favouriteRoutes={favouriteRoutes}
        favouriteTools={favouriteTools}
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        onToggleFavourite={toggleFavourite}
        publicTools={visiblePublicTools}
      />

      <Container
        component="main"
        sx={{
          flex: 1,
          py: 2,
          maxWidth: { xs: '100%', md: '70%', xl: 1200 },
          '@media (min-width: 800px) and (max-width: 1200px)': {
            maxWidth: '90%'
          }
        }}
      >
        <LandingPageHeader onOpenQuickAccess={() => setIsDrawerOpen(true)} />

        <Stack spacing={5}>
          {favouriteTools.length > 0 && (
            <ToolSection
              backgroundColour="#eef3ee"
              borderColour="#c2d4c2"
              headingId={FAVOURITES_SECTION_ID}
              icon={<StarIcon sx={{ color: FAVOURITES_COLOUR, fontSize: 18 }} />}
              isFavourite={route => favouriteRoutes.includes(route)}
              onToggleFavourite={toggleFavourite}
              title="My Favourites"
              tools={favouriteTools}
            />
          )}
          {visibleBcpsTools.length > 0 && (
            <ToolSection
              backgroundColour="#d9e8f5"
              borderColour="#A8C5E0"
              headingId={BCPS_SECTION_ID}
              icon={<LockOutlinedIcon sx={{ color: 'primary.main', fontSize: 18 }} />}
              isFavourite={route => favouriteRoutes.includes(route)}
              onToggleFavourite={toggleFavourite}
              title="BCPS Access Only"
              tools={visibleBcpsTools}
            />
          )}
          {visiblePublicTools.length > 0 && (
            <ToolSection
              backgroundColour="#fff7ed"
              borderColour="#FDDCB5"
              headingId={PUBLIC_SECTION_ID}
              icon={<PublicOutlinedIcon sx={{ color: PUBLIC_TOOL_ICON_COLOUR, fontSize: 18 }} />}
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

export default LandingPage
