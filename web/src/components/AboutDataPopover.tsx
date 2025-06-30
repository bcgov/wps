import InfoIcon from '@mui/icons-material/Info'
import { Box } from '@mui/material'
import Popover from '@mui/material/Popover'
import Typography from '@mui/material/Typography'
import { INFO_PANEL_CONTENT_BACKGROUND, theme } from 'app/theme'
import * as React from 'react'

interface AboutDataPopoverProps<T = {}> {
  content: (props: T) => React.ReactNode
  props?: T
  maxWidth?: number
  testId?: string
}

const AboutDataPopover = <T,>({
  content,
  props = {} as T,
  maxWidth = 350,
  testId = 'about-data-popover'
}: AboutDataPopoverProps<T>) => {
  const [anchorEl, setAnchorEl] = React.useState<HTMLElement | null>(null)

  const handlePopoverOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handlePopoverClose = () => {
    setAnchorEl(null)
  }

  const open = Boolean(anchorEl)

  return (
    <Box data-testid={testId}>
      <Typography
        data-testid="about-data-trigger"
        fontSize={'0.75rem'}
        onClick={handlePopoverOpen}
        sx={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}
      >
        <InfoIcon sx={{ marginRight: theme.spacing(1), color: '#5686E1' }} />
        About this data
      </Typography>
      <Popover
        id="about-data-popover"
        open={open}
        anchorEl={anchorEl}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left'
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'left'
        }}
        onClose={handlePopoverClose}
        disableRestoreFocus
        slotProps={{
          paper: {
            sx: {
              maxWidth,
              backgroundColor: INFO_PANEL_CONTENT_BACKGROUND,
              overflowY: 'auto',
              maxHeight: '80%'
            }
          }
        }}
      >
        <Typography sx={{ padding: theme.spacing(1), fontWeight: 'bold', fontSize: '1rem' }}>
          About This Data
        </Typography>
        <Box style={{ padding: theme.spacing(2), fontSize: '0.9rem' }} data-testid="about-data-content">
          {content(props)}
        </Box>
      </Popover>
    </Box>
  )
}

export default AboutDataPopover
