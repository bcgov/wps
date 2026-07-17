import LaunchIcon from '@mui/icons-material/Launch'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import type { ToolInfo } from 'features/landingPage/toolInfo'
import FavouriteButton from './FavouriteButton'
import { getManagingTeam, ICON_TILE_RADIUS, TOOL_ROW_RADIUS } from './landingPagePreviewConfig'

interface ToolRowProps {
  isFavourite: boolean
  onToggleFavourite: () => void
  tool: ToolInfo
}

const ToolRow = ({ isFavourite, onToggleFavourite, tool }: ToolRowProps) => {
  const isExternal = tool.route.startsWith('http')
  const managingTeam = getManagingTeam(tool)

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
        gridTemplateColumns: { xs: '1fr', sm: 'minmax(260px, 0.85fr) minmax(360px, 1.65fr) auto' },
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
            Managed by: {managingTeam}
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

export default ToolRow
