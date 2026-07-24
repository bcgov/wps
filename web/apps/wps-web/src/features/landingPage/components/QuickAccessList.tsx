import Box from '@mui/material/Box'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Typography from '@mui/material/Typography'
import type { ToolInfo } from 'features/landingPage/toolInfo'
import { Link as RouterLink } from 'react-router-dom'
import FavouriteButton from './FavouriteButton'
import ToolIconTile from './ToolIconTile'

interface QuickAccessListProps {
  favouriteRoutes: string[]
  headingColor: string
  onNavigate: () => void
  onToggleFavourite: (route: string) => void
  title: string
  tools: ToolInfo[]
}

const QuickAccessList = ({
  favouriteRoutes,
  headingColor,
  onNavigate,
  onToggleFavourite,
  title,
  tools
}: QuickAccessListProps) => (
  <Box>
    <Typography sx={{ color: headingColor, fontSize: '0.875rem', fontWeight: 700, px: 2, pb: 0.5, pt: 1.5 }}>
      {title.toUpperCase()}
    </Typography>
    <List disablePadding>
      {tools.map(tool => {
        const isExternal = tool.isExternal === true
        const content = (
          <>
            <ListItemIcon sx={{ minWidth: 46 }}>
              <ToolIconTile icon={tool.icon} iconScale={0.82} size={32} />
            </ListItemIcon>
            <ListItemText primary={tool.name} slotProps={{ primary: { sx: { fontSize: '14px' } } }} />
          </>
        )

        return (
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
            {isExternal ? (
              <ListItemButton href={tool.route} onClick={onNavigate} rel="noreferrer" sx={{ pr: 7 }} target="_blank">
                {content}
              </ListItemButton>
            ) : (
              <ListItemButton component={RouterLink} onClick={onNavigate} sx={{ pr: 7 }} to={tool.route}>
                {content}
              </ListItemButton>
            )}
          </ListItem>
        )
      })}
    </List>
  </Box>
)

export default QuickAccessList
