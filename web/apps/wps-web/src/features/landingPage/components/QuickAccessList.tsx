import Box from '@mui/material/Box'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Typography from '@mui/material/Typography'
import type { ToolInfo } from 'features/landingPage/toolInfo'
import FavouriteButton from './FavouriteButton'

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
            <ListItemButton
              href={tool.route}
              onClick={onNavigate}
              rel={isExternal ? 'noreferrer' : undefined}
              sx={{ pr: 7 }}
              target={isExternal ? '_blank' : undefined}
            >
              <ListItemIcon sx={{ minWidth: 42 }}>{tool.icon}</ListItemIcon>
              <ListItemText
                primary={tool.name}
                slotProps={{ primary: { sx: { fontSize: '0.875rem', fontWeight: 600 } } }}
              />
            </ListItemButton>
          </ListItem>
        )
      })}
    </List>
  </Box>
)

export default QuickAccessList
