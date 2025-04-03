import * as React from 'react'
import Popover from '@mui/material/Popover'
import Typography from '@mui/material/Typography'
import InfoIcon from '@mui/icons-material/Info'
import { theme } from 'app/theme'

interface AboutDataPopoverProps<T = {}> {
  content: (props: T) => React.ReactNode
  props?: T
  backgroundColor?: string
}

const AboutDataPopover = <T,>({ content, props = {} as T, backgroundColor }: AboutDataPopoverProps<T>) => {
  const [anchorEl, setAnchorEl] = React.useState<HTMLElement | null>(null)

  const handlePopoverOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handlePopoverClose = () => {
    setAnchorEl(null)
  }

  const open = Boolean(anchorEl)

  return (
    <div data-testid="about-data-popover">
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
        onClose={handlePopoverClose}
        disableRestoreFocus
        slotProps={{ paper: { sx: { maxWidth: 350, backgroundColor } } }}
      >
        <Typography sx={{ padding: theme.spacing(1), fontWeight: 'bold', fontSize: '1rem' }}>
          About This Data
        </Typography>
        <div style={{ padding: theme.spacing(2), fontSize: '0.9rem' }} data-testid="about-data-content">
          {content(props)}
        </div>
      </Popover>
    </div>
  )
}

export default AboutDataPopover
