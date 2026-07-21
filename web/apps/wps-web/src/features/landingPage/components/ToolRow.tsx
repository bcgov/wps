import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import Link from '@mui/material/Link'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { getFeedback } from '@sentry/react'
import type { ToolInfo } from 'features/landingPage/toolInfo'
import type React from 'react'
import { TOOL_ROW_RADIUS } from '../landingPageConfig'
import FavouriteButton from './FavouriteButton'
import ToolIconTile from './ToolIconTile'

interface ToolRowProps {
  isFavourite: boolean
  onToggleFavourite: () => void
  tool: ToolInfo
}

const ToolRow = ({ isFavourite, onToggleFavourite, tool }: ToolRowProps) => {
  const isExternal = tool.isExternal === true
  const openFeedbackForm = async (event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault()
    const feedback = getFeedback()
    if (!feedback) {
      return
    }

    const form = await feedback.createForm()
    form.appendToDom()
    form.open()
  }

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
        minHeight: { sm: 120 },
        p: 2
      }}
    >
      <Stack direction="row" spacing={1.5} sx={{ alignItems: 'flex-start', minWidth: 0, pr: { sm: 2 } }}>
        <ToolIconTile icon={tool.icon} />
        <Box sx={{ minWidth: 0, width: '100%', display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'flex-start', justifyContent: 'space-between' }}>
            <Typography
              component="h3"
              sx={{ fontWeight: 700, lineHeight: 1.35, pt: 1, pb: { sm: 1, md: 3 } }}
              variant="body1"
            >
              <Link
                color="inherit"
                href={tool.route}
                rel={isExternal ? 'noreferrer' : undefined}
                target={isExternal ? '_blank' : undefined}
                underline="hover"
              >
                {tool.name}
              </Link>
            </Typography>
            <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center', flex: '0 0 auto' }}>
              {tool.isBeta && <Chip color="primary" label="Beta" size="small" variant="outlined" />}
              <FavouriteButton isFavourite={isFavourite} onToggle={onToggleFavourite} toolName={tool.name} />
            </Stack>
          </Stack>
          {/* <Typography color="text.primary" sx={{ display: 'block', mt: 1.25 }} variant="body2">
            {tool.subheading}
          </Typography> */}
          <Typography color="text.secondary" sx={{ display: 'block', mt: 'auto', pt: 1 }} variant="caption">
            Managed by:{' '}
            <Link
              href={tool.managedBy.href ?? '#'}
              onClick={tool.managedBy.opensFeedback ? openFeedbackForm : undefined}
              underline="hover"
            >
              {tool.managedBy.name}
            </Link>
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
