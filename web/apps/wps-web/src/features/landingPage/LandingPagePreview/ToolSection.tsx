import Box from '@mui/material/Box'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import type { ToolInfo } from 'features/landingPage/toolInfo'
import type { ReactNode } from 'react'
import { SECTION_RADIUS } from './landingPagePreviewConfig'
import ToolRow from './ToolRow'

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

export default ToolSection
