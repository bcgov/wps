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

export default QuickAccessList
