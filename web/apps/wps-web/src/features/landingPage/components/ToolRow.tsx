import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import MuiLink from '@mui/material/Link'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { openFeedbackForm } from '@wps/ui/openFeedbackForm'
import type { ToolInfo } from 'features/landingPage/toolInfo'
import type React from 'react'
import { Link as RouterLink } from 'react-router-dom'
import FavouriteButton from './FavouriteButton'
import ToolIconTile from './ToolIconTile'

const TOOL_ROW_RADIUS = '16px'

interface ToolRowProps {
  isFavourite: boolean
  onToggleFavourite: () => void
  tool: ToolInfo
}

const ToolRow = ({ isFavourite, onToggleFavourite, tool }: ToolRowProps) => {
  const isExternal = tool.isExternal === true
  const handleFeedbackLinkClick = async (event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault()
    await openFeedbackForm()
  }

  return (
    <Paper
      component="article"
      variant="outlined"
      sx={{
        borderColor: 'grey.300',
        borderRadius: TOOL_ROW_RADIUS,
        display: 'grid',
        gap: { xs: 2, md: 0 },
        gridTemplateColumns: { xs: '1fr', md: 'minmax(260px, 0.85fr) minmax(360px, 1.65fr) auto' },
        minHeight: { md: 110 },
        p: 2
      }}
    >
      <Stack direction="row" spacing={1.5} sx={{ alignItems: 'flex-start', minWidth: 0, pr: { md: 2 } }}>
        <ToolIconTile icon={tool.icon} />
        <Box sx={{ minWidth: 0, width: '100%', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <Typography
              component="h3"
              sx={{
                fontWeight: 700,
                lineHeight: 1.35,
                pt: 1,
                pb: { sm: 1, md: 3 }
              }}
              variant="body1"
            >
              {isExternal ? (
                <MuiLink color="inherit" href={tool.route} rel="noreferrer" target="_blank" underline="hover">
                  {tool.name}
                </MuiLink>
              ) : (
                <MuiLink color="inherit" component={RouterLink} to={tool.route} underline="hover">
                  {tool.name}
                </MuiLink>
              )}
            </Typography>
            <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center', flex: '0 0 auto' }}>
              {tool.isBeta && <Chip color="primary" label="Beta" size="small" variant="outlined" />}
              <FavouriteButton isFavourite={isFavourite} onToggle={onToggleFavourite} toolName={tool.name} />
            </Stack>
          </Stack>
          <Typography color="text.secondary" sx={{ display: 'block', mt: 'auto', pt: 1 }} variant="caption">
            Managed by:{' '}
            <MuiLink
              href={tool.managedBy.href ?? '#'}
              onClick={tool.managedBy.opensFeedback ? handleFeedbackLinkClick : undefined}
              underline="hover"
            >
              {tool.managedBy.name}
            </MuiLink>
          </Typography>
        </Box>
      </Stack>

      <Box
        sx={{
          borderColor: 'grey.200',
          borderLeftStyle: { md: 'solid' },
          borderLeftWidth: { md: 1 },
          color: 'text.secondary',
          minWidth: 0,
          px: { md: 2 },
          '& .MuiTypography-root': {
            color: 'black',
            fontSize: { xs: '0.8125rem', sm: '0.875rem', md: '0.9rem' },
            lineHeight: 1.55
          }
        }}
      >
        {tool.description}
      </Box>

      {isExternal ? (
        <Button
          href={tool.route}
          rel="noreferrer"
          sx={{
            alignSelf: 'center',
            borderRadius: '10px',
            justifySelf: { xs: 'stretch', md: 'end' },
            ml: { md: 1 },
            whiteSpace: 'nowrap'
          }}
          target="_blank"
          variant="contained"
        >
          Open
        </Button>
      ) : (
        <Button
          component={RouterLink}
          sx={{
            alignSelf: 'center',
            borderRadius: '10px',
            justifySelf: { xs: 'stretch', md: 'end' },
            ml: { md: 1 },
            whiteSpace: 'nowrap'
          }}
          to={tool.route}
          variant="contained"
        >
          Open
        </Button>
      )}
    </Paper>
  )
}

export default ToolRow
