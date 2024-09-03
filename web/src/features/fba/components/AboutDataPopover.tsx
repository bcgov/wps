import * as React from 'react'
import Popover from '@mui/material/Popover'
import Typography from '@mui/material/Typography'
import InfoIcon from '@mui/icons-material/Info'
import { theme } from 'app/theme'

interface AboutDataProps {
  advisoryThreshold: number
}

const AboutDataPopover = ({ advisoryThreshold }: AboutDataProps) => {
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
        <InfoIcon sx={{ marginRight: theme.spacing(1), color: '#4681f4' }}></InfoIcon>
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
        slotProps={{ paper: { sx: { maxWidth: 350, backgroundColor: '#EEEEEE' } } }}
      >
        <Typography
          sx={{
            padding: theme.spacing(1),
            fontWeight: 'bold',
            fontSize: '1rem'
          }}
        >
          About This Data
        </Typography>
        <div
          style={{ paddingBottom: theme.spacing(3), paddingRight: theme.spacing(2), fontSize: '0.9rem' }}
          data-testid="about-data-content"
        >
          <ul style={{ margin: 0 }}>
            <li>
              A Fire Zone is under a Fire Behaviour Advisory if greater than {advisoryThreshold}% of the combustible
              land (trees, grass, slash) is forecast to have a Head Fire Intensity between 4,000 and 10,000 kW/m.
            </li>
            <br />
            <li>
              A Fire Zone is under a Fire Behaviour Warning if greater than {advisoryThreshold}% of the combustible land
              is forecast to have a Head Fire Intensity greater than 10,000 kW/m.
            </li>
            <br />
            <li>
              The fuel types chosen for the text bulletin are the three most common fuel types in a zone that meet or
              exceed the Fire Behaviour Advisory threshold of 4,000 kW/m.
            </li>
          </ul>
        </div>
      </Popover>
    </div>
  )
}

export default AboutDataPopover
