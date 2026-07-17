import Box from '@mui/material/Box'
import Link from '@mui/material/Link'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { TECH_SERVICES_EMAIL } from '../landingPageConfig'

const SupportSection = () => (
  <Box sx={{ borderTop: 1, borderColor: 'divider', mt: 'auto', p: 2 }}>
    <Typography color="primary" sx={{ fontSize: '0.75rem', fontWeight: 700, mb: 1.5 }}>
      SUPPORT
    </Typography>
    <Stack spacing={1.5}>
      <Typography color="text.secondary" sx={{ fontSize: '0.8125rem' }} variant="body2">
        To report bugs or receive support on technical issues, please use the Submit Feedback in-app functionality.
      </Typography>
      <Box>
        <Typography sx={{ fontSize: '0.8125rem', fontWeight: 700 }} variant="body2">
          After-hours support:
        </Typography>
        <Link href={`mailto:${TECH_SERVICES_EMAIL}`} sx={{ fontSize: '0.8125rem', overflowWrap: 'anywhere' }}>
          {TECH_SERVICES_EMAIL}
        </Link>
      </Box>
    </Stack>
  </Box>
)

export default SupportSection
