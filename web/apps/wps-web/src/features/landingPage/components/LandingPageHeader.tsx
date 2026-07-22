import MenuIcon from '@mui/icons-material/Menu'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Link from '@mui/material/Link'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { MS_TEAMS_SPRINT_REVIEW_URL, SPRINT_REVIEW_BOARD_URL } from '@wps/utils/env'

interface LandingPageHeaderProps {
  onOpenQuickAccess: () => void
}

const LandingPageHeader = ({ onOpenQuickAccess }: LandingPageHeaderProps) => (
  <Box
    component="header"
    sx={{
      mb: { xs: 4, sm: 5 }
    }}
  >
    <Stack
      direction={{ xs: 'column', sm: 'row' }}
      spacing={2}
      sx={{ alignItems: { xs: 'flex-start', sm: 'center' }, justifyContent: 'space-between', mb: { xs: 2, sm: 1.5 } }}
    >
      <Tooltip title="Open quick access">
        <Button
          aria-label="Open quick access"
          onClick={onOpenQuickAccess}
          startIcon={<MenuIcon />}
          sx={{ alignSelf: { xs: 'stretch', sm: 'center' } }}
          variant="outlined"
        >
          Quick Access
        </Button>
      </Tooltip>
      <Box
        alt="B.C. Wildfire Service"
        component="img"
        src="/images/BCID_H_RGB_pos.png"
        sx={{ display: 'block', height: 'auto', maxWidth: 250, width: '65vw' }}
      />
    </Stack>

    <Stack spacing={1.25}>
      <Typography component="h1" sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' }, fontWeight: 700 }}>
        Predictive Services Tools &amp; Applications
      </Typography>
      <Typography color="text.secondary" sx={{ mt: 1.5, maxWidth: 960 }} variant="body2">
        BCPS Access Only tools require a BC Government account, while Public Access apps are open to all users. Pin any
        app using the pushpin icon to save it to your personal <strong>My Favourites</strong> section.
      </Typography>
      <Typography color="text.secondary" sx={{ mt: 1, maxWidth: 960 }} variant="body2">
        Collaborate with us by adding our biweekly{' '}
        <Tooltip arrow describeChild placement="bottom" title="Wednesdays at 1:00 PM on non-pay weeks">
          <Link href={MS_TEAMS_SPRINT_REVIEW_URL} rel="noreferrer" target="_blank">
            Sprint Reviews
          </Link>
        </Tooltip>{' '}
        and{' '}
        <Link href={SPRINT_REVIEW_BOARD_URL} rel="noreferrer" target="_blank">
          Collaboard
        </Link>{' '}
        to your calendar and bookmarks.
      </Typography>
    </Stack>
  </Box>
)

export default LandingPageHeader
