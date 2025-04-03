import * as React from 'react'
import Popover from '@mui/material/Popover'
import Typography from '@mui/material/Typography'
import InfoIcon from '@mui/icons-material/Info'
import { theme } from '@/app/theme'

const AboutDataPopover = () => {
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
        <InfoIcon sx={{ marginRight: theme.spacing(1), color: '#5686E1' }}></InfoIcon>
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
        slotProps={{ paper: { sx: { maxWidth: 350 } } }}
      >
        <Typography
          sx={{
            paddingLeft: theme.spacing(2),
            paddingTop: theme.spacing(1),
            fontWeight: 'bold',
            fontSize: '1rem'
          }}
        >
          About This Data
        </Typography>
        <div style={{ padding: theme.spacing(2), fontSize: '0.9rem' }} data-testid="about-data-content">
          <p>
            Forecasted weather outputs are for 13:00 and FWI Indices are for 17:00 PDT. These fire behaviour
            calculations assume flat terrain.
          </p>
          <p>Weather and fire behaviour indices are sourced from the Wildfire One API.</p>
          <p>
            Values are calculated using the{' '}
            <a target="_blank" rel="noopener noreferrer" href="https://github.com/cffdrs/cffdrs_r">
              Canadian Forest Fire Danger Rating System R Library
            </a>{' '}
            and are intended to provide general guidance for Fire Behaviour Advisories.
          </p>
          <p>
            Constants for crown fuel load are taken from &quot;Development and Structure of the Canadian Forest Fire
            Behaviour Prediction System&quot; from Forestry Canada Fire Danger Group, Information Report ST-X-3, 1992.
          </p>
          <p>
            If you have any questions about how values are calculated, please{' '}
            <a href="mailto: bcws.predictiveservices@gov.bc.ca?subject=Predictive Services Unit - Fire Behaviour Advisory Calculator">
              contact us.
            </a>
          </p>
        </div>
      </Popover>
    </div>
  )
}

export default AboutDataPopover
