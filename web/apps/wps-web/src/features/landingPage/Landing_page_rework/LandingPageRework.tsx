import CloseIcon from '@mui/icons-material/Close'
import LaunchIcon from '@mui/icons-material/Launch'
import LockOutlinedIcon from '@mui/icons-material/LockOutlined'
import MenuIcon from '@mui/icons-material/Menu'
import PublicOutlinedIcon from '@mui/icons-material/PublicOutlined'
import PushPinIcon from '@mui/icons-material/PushPin'
import PushPinOutlinedIcon from '@mui/icons-material/PushPinOutlined'
import StarIcon from '@mui/icons-material/Star'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import Container from '@mui/material/Container'
import Divider from '@mui/material/Divider'
import Drawer from '@mui/material/Drawer'
import IconButton from '@mui/material/IconButton'
import Link from '@mui/material/Link'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { MS_TEAMS_SPRINT_REVIEW_URL, SPRINT_REVIEW_BOARD_URL } from '@wps/utils/env'
import Footer from 'features/landingPage/components/Footer'
import { fbpGoInfo, type ToolInfo, toolInfos } from 'features/landingPage/toolInfo'
import type { ReactNode } from 'react'
import { useEffect, useState } from 'react'

const BCWS_SECTION_ID = 'bcws-access-only-heading'
const FAVOURITES_SECTION_ID = 'favourites-heading'
const PUBLIC_SECTION_ID = 'public-access-heading'
export const LANDING_PAGE_FAVOURITES_STORAGE_KEY = 'wps-landing-page-favourites'
const ICON_TILE_RADIUS = '14px'
const SECTION_RADIUS = '18px'
const TOOL_ROW_RADIUS = '16px'
const PREDICTIVE_SERVICES_EMAIL = 'BCWS.PredictiveServices@gov.bc.ca'
const TECH_SERVICES_EMAIL = 'BCWS.TechServices@gov.bc.ca'
const publicTools = [fbpGoInfo]
const bcwsTools = toolInfos.filter(tool => tool.route !== fbpGoInfo.route)

const readFavouriteRoutes = () => {
  try {
    const storedValue = localStorage.getItem(LANDING_PAGE_FAVOURITES_STORAGE_KEY)
    if (!storedValue) {
      return []
    }

    const parsedValue: unknown = JSON.parse(storedValue)
    if (!Array.isArray(parsedValue)) {
      return []
    }

    return toolInfos.filter(tool => parsedValue.includes(tool.route)).map(tool => tool.route)
  } catch {
    return []
  }
}

const storeFavouriteRoutes = (favouriteRoutes: string[]) => {
  try {
    localStorage.setItem(LANDING_PAGE_FAVOURITES_STORAGE_KEY, JSON.stringify(favouriteRoutes))
  } catch {
    return
  }
}

interface FavouriteButtonProps {
  isFavourite: boolean
  onToggle: () => void
  toolName: string
}

const FavouriteButton = ({ isFavourite, onToggle, toolName }: FavouriteButtonProps) => {
  const action = isFavourite ? 'Remove' : 'Add'
  const label = `${action} ${toolName} ${isFavourite ? 'from' : 'to'} favourites`

  return (
    <Tooltip title={label}>
      <IconButton aria-label={label} color={isFavourite ? 'primary' : 'default'} onClick={onToggle} size="small">
        {isFavourite ? <PushPinIcon fontSize="small" /> : <PushPinOutlinedIcon fontSize="small" />}
      </IconButton>
    </Tooltip>
  )
}

interface ToolRowProps {
  isFavourite: boolean
  onToggleFavourite: () => void
  tool: ToolInfo
}

const ToolRow = ({ isFavourite, onToggleFavourite, tool }: ToolRowProps) => {
  const isExternal = tool.route.startsWith('http')

  return (
    <Paper
      component="article"
      variant="outlined"
      sx={{
        alignItems: { sm: 'stretch' },
        borderColor: 'grey.300',
        borderRadius: TOOL_ROW_RADIUS,
        display: 'grid',
        gap: { xs: 2, sm: 0 },
        gridTemplateColumns: { xs: '1fr', sm: 'minmax(240px, 0.9fr) minmax(280px, 1.4fr) auto' },
        p: 2
      }}
    >
      <Stack direction="row" spacing={1.5} sx={{ alignItems: 'flex-start', minWidth: 0, pr: { sm: 2 } }}>
        <Box
          sx={{
            alignItems: 'center',
            bgcolor: 'grey.50',
            borderRadius: ICON_TILE_RADIUS,
            display: 'flex',
            flex: '0 0 auto',
            height: 48,
            justifyContent: 'center',
            width: 48
          }}
        >
          {tool.icon}
        </Box>
        <Box sx={{ minWidth: 0, width: '100%' }}>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <Typography component="h3" sx={{ fontWeight: 700, lineHeight: 1.35 }} variant="body1">
              {tool.name}
            </Typography>
            <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center', flex: '0 0 auto' }}>
              {tool.isBeta && <Chip color="primary" label="Beta" size="small" variant="outlined" />}
              <FavouriteButton isFavourite={isFavourite} onToggle={onToggleFavourite} toolName={tool.name} />
            </Stack>
          </Stack>
          <Typography color="text.secondary" sx={{ display: 'block', mt: 0.75 }} variant="caption">
            Managed by: (Team Name)
          </Typography>
        </Box>
      </Stack>

      <Box
        sx={{
          borderColor: 'grey.200',
          borderLeftStyle: { sm: 'solid' },
          borderLeftWidth: { sm: 1 },
          color: 'text.secondary',
          minWidth: 0,
          px: { sm: 2 },
          '& .MuiTypography-root': {
            color: 'inherit',
            fontSize: '0.875rem',
            lineHeight: 1.55
          }
        }}
      >
        {tool.description}
      </Box>

      <Button
        endIcon={<LaunchIcon fontSize="small" />}
        href={tool.route}
        rel={isExternal ? 'noreferrer' : undefined}
        sx={{ alignSelf: 'center', justifySelf: { xs: 'stretch', sm: 'end' }, ml: { sm: 1 }, whiteSpace: 'nowrap' }}
        target={isExternal ? '_blank' : undefined}
        variant="contained"
      >
        Open
      </Button>
    </Paper>
  )
}

interface ToolSectionProps {
  backgroundColor: string
  headingId: string
  icon: ReactNode
  isFavourite: (route: string) => boolean
  onToggleFavourite: (route: string) => void
  title: string
  tools: ToolInfo[]
}

const ToolSection = ({
  backgroundColor,
  headingId,
  icon,
  isFavourite,
  onToggleFavourite,
  title,
  tools
}: ToolSectionProps) => (
  <Box component="section" aria-labelledby={headingId}>
    <Stack direction="row" spacing={1} sx={{ alignItems: 'center', mb: 1.5 }}>
      <Box
        sx={{
          alignItems: 'center',
          bgcolor: backgroundColor,
          borderRadius: '50%',
          color: 'primary.main',
          display: 'flex',
          height: 30,
          justifyContent: 'center',
          width: 30
        }}
      >
        {icon}
      </Box>
      <Typography component="h2" id={headingId} sx={{ fontSize: '1.125rem', fontWeight: 700 }}>
        {title}
      </Typography>
    </Stack>
    <Stack
      spacing={1.5}
      sx={{
        bgcolor: backgroundColor,
        border: 1,
        borderColor: 'grey.300',
        borderRadius: SECTION_RADIUS,
        p: { xs: 1.5, sm: 2 }
      }}
    >
      {tools.map(tool => (
        <ToolRow
          isFavourite={isFavourite(tool.route)}
          key={tool.route}
          onToggleFavourite={() => onToggleFavourite(tool.route)}
          tool={tool}
        />
      ))}
    </Stack>
  </Box>
)

interface QuickAccessListProps {
  favouriteRoutes: string[]
  onNavigate: () => void
  onToggleFavourite: (route: string) => void
  title: string
  tools: ToolInfo[]
}

const QuickAccessList = ({ favouriteRoutes, onNavigate, onToggleFavourite, title, tools }: QuickAccessListProps) => (
  <Box>
    <Typography color="primary" sx={{ fontSize: '0.75rem', fontWeight: 700, px: 2, pb: 0.5, pt: 1.5 }}>
      {title.toUpperCase()}
    </Typography>
    <List disablePadding>
      {tools.map(tool => (
        <ListItem
          disablePadding
          key={`${title}-${tool.route}`}
          secondaryAction={
            <FavouriteButton
              isFavourite={favouriteRoutes.includes(tool.route)}
              onToggle={() => onToggleFavourite(tool.route)}
              toolName={tool.name}
            />
          }
        >
          <ListItemButton href={tool.route} onClick={onNavigate} sx={{ pr: 7 }}>
            <ListItemIcon sx={{ minWidth: 42 }}>{tool.icon}</ListItemIcon>
            <ListItemText
              primary={tool.name}
              slotProps={{ primary: { sx: { fontSize: '0.875rem', fontWeight: 600 } } }}
            />
          </ListItemButton>
        </ListItem>
      ))}
    </List>
  </Box>
)

const SupportSection = () => (
  <Box sx={{ borderTop: 1, borderColor: 'divider', mt: 'auto', p: 2 }}>
    <Typography color="primary" sx={{ fontSize: '0.75rem', fontWeight: 700, mb: 1.5 }}>
      SUPPORT
    </Typography>
    <Stack spacing={1.5}>
      <Box>
        <Typography sx={{ fontSize: '0.8125rem', fontWeight: 700 }} variant="body2">
          Contact Us:
        </Typography>
        <Link href={`mailto:${PREDICTIVE_SERVICES_EMAIL}`} sx={{ fontSize: '0.8125rem', overflowWrap: 'anywhere' }}>
          {PREDICTIVE_SERVICES_EMAIL}
        </Link>
      </Box>
      <Box>
        <Typography sx={{ fontSize: '0.8125rem', fontWeight: 700 }} variant="body2">
          After Hours Support:
        </Typography>
        <Link href={`mailto:${TECH_SERVICES_EMAIL}`} sx={{ fontSize: '0.8125rem', overflowWrap: 'anywhere' }}>
          {TECH_SERVICES_EMAIL}
        </Link>
      </Box>
    </Stack>
  </Box>
)

const LandingPageRework = () => {
  const [favouriteRoutes, setFavouriteRoutes] = useState<string[]>(readFavouriteRoutes)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const favouriteTools = toolInfos.filter(tool => favouriteRoutes.includes(tool.route))
  const visibleBcwsTools = bcwsTools.filter(tool => !favouriteRoutes.includes(tool.route))
  const visiblePublicTools = publicTools.filter(tool => !favouriteRoutes.includes(tool.route))

  useEffect(() => {
    document.title = 'Landing Page Rework | BC Wildfire Service'
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
      <Drawer onClose={() => setIsDrawerOpen(false)} open={isDrawerOpen}>
        <Box
          component="nav"
          aria-label="Quick access"
          sx={{ display: 'flex', flexDirection: 'column', height: '100%', width: { xs: 300, sm: 340 } }}
        >
          <Stack
            direction="row"
            sx={{
              alignItems: 'center',
              borderBottom: 1,
              borderColor: 'divider',
              justifyContent: 'space-between',
              p: 2
            }}
          >
            <Typography sx={{ fontWeight: 700 }}>Quick Access</Typography>
            <Tooltip title="Close quick access">
              <IconButton aria-label="Close quick access" onClick={() => setIsDrawerOpen(false)} size="small">
                <CloseIcon />
              </IconButton>
            </Tooltip>
          </Stack>
          <Box sx={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
            {favouriteTools.length > 0 && (
              <QuickAccessList
                favouriteRoutes={favouriteRoutes}
                onNavigate={() => setIsDrawerOpen(false)}
                onToggleFavourite={toggleFavourite}
                title="My Favourites"
                tools={favouriteTools}
              />
            )}
            {visibleBcwsTools.length > 0 && (
              <>
                <Divider />
                <QuickAccessList
                  favouriteRoutes={favouriteRoutes}
                  onNavigate={() => setIsDrawerOpen(false)}
                  onToggleFavourite={toggleFavourite}
                  title="BCWS Access Only"
                  tools={visibleBcwsTools}
                />
              </>
            )}
            {visiblePublicTools.length > 0 && (
              <>
                <Divider />
                <QuickAccessList
                  favouriteRoutes={favouriteRoutes}
                  onNavigate={() => setIsDrawerOpen(false)}
                  onToggleFavourite={toggleFavourite}
                  title="Public Access"
                  tools={visiblePublicTools}
                />
              </>
            )}
          </Box>
          <SupportSection />
        </Box>
      </Drawer>

      <Container component="main" maxWidth="md" sx={{ flex: 1, py: { xs: 3, sm: 5 } }}>
        <Stack direction="row" spacing={2} sx={{ alignItems: 'flex-start', mb: { xs: 4, sm: 5 } }}>
          <Tooltip title="Open quick access">
            <IconButton aria-label="Open quick access" onClick={() => setIsDrawerOpen(true)} sx={{ mt: 0.5 }}>
              <MenuIcon />
            </IconButton>
          </Tooltip>
          <Box>
            <Box
              alt="B.C. Wildfire Service"
              component="img"
              src="/images/bc-wilderfire-service-logo.png"
              sx={{ display: 'block', height: 'auto', mb: 2, maxWidth: 220, width: '65vw' }}
            />
            <Typography component="h1" sx={{ fontSize: { xs: '1rem', sm: '1.25rem' }, fontWeight: 700 }}>
              Predictive Services Tools &amp; Applications
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1.5, maxWidth: 760 }} variant="body2">
              BCPS Access Only tools require a BC Government account, while Public Access apps are open to all users.
              Pin any app using the pushpin icon to save it to your personal <strong>My Favourites</strong> section.
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1, maxWidth: 760 }} variant="body2">
              Collaborate with us by adding our biweekly{' '}
              <Tooltip arrow describeChild placement="bottom" title="Wednesdays at 1:00 PM on non-pay weeks">
                <Link href={MS_TEAMS_SPRINT_REVIEW_URL} rel="noreferrer" target="_blank">
                  Sprint Reviews
                </Link>
              </Tooltip>{' '}
              and{' '}
              <Link href={SPRINT_REVIEW_BOARD_URL} rel="noreferrer" target="_blank">
                Collaboard
              </Link>{' '}
              to your calendar and bookmarks.
            </Typography>
          </Box>
        </Stack>

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

export default LandingPageRework
