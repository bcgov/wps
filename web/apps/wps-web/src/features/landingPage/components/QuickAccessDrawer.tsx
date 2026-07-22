import CloseIcon from '@mui/icons-material/Close'
import Box from '@mui/material/Box'
import Divider from '@mui/material/Divider'
import Drawer from '@mui/material/Drawer'
import IconButton from '@mui/material/IconButton'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { FAVOURITES_COLOUR, PUBLIC_TOOL_ICON_COLOUR } from 'features/landingPage/landingPageConfig'
import type { ToolInfo } from 'features/landingPage/toolInfo'
import QuickAccessList from './QuickAccessList'
import SupportSection from './SupportSection'

interface QuickAccessDrawerProps {
  favouriteRoutes: string[]
  favouriteTools: ToolInfo[]
  isOpen: boolean
  onClose: () => void
  onToggleFavourite: (route: string) => void
  publicTools: ToolInfo[]
  bcwsTools: ToolInfo[]
}

const QuickAccessDrawer = ({
  favouriteRoutes,
  favouriteTools,
  isOpen,
  onClose,
  onToggleFavourite,
  publicTools,
  bcwsTools
}: QuickAccessDrawerProps) => (
  <Drawer onClose={onClose} open={isOpen}>
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
          <IconButton aria-label="Close quick access" onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Tooltip>
      </Stack>
      <Box sx={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
        {favouriteTools.length > 0 && (
          <QuickAccessList
            favouriteRoutes={favouriteRoutes}
            headingColor={FAVOURITES_COLOUR}
            onNavigate={onClose}
            onToggleFavourite={onToggleFavourite}
            title="My Favourites"
            tools={favouriteTools}
          />
        )}
        {bcwsTools.length > 0 && (
          <>
            <Divider />
            <QuickAccessList
              favouriteRoutes={favouriteRoutes}
              headingColor="primary.main"
              onNavigate={onClose}
              onToggleFavourite={onToggleFavourite}
              title="BCPS Access Only"
              tools={bcwsTools}
            />
          </>
        )}
        {publicTools.length > 0 && (
          <>
            <Divider />
            <QuickAccessList
              favouriteRoutes={favouriteRoutes}
              headingColor={PUBLIC_TOOL_ICON_COLOUR}
              onNavigate={onClose}
              onToggleFavourite={onToggleFavourite}
              title="Public Access"
              tools={publicTools}
            />
          </>
        )}
      </Box>
      <SupportSection />
    </Box>
  </Drawer>
)

export default QuickAccessDrawer
