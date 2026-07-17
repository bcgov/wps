import Box from '@mui/material/Box'
import Link from '@mui/material/Link'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { PREDICTIVE_SERVICES_EMAIL, TECH_SERVICES_EMAIL } from './landingPagePreviewConfig'

const SupportSection = () => (
  <Box sx={{ borderTop: 1, borderColor: 'divider', mt: 'auto', p: 2 }}>
    <Typography color="primary" sx={{ fontSize: '0.75rem', fontWeight: 700, mb: 1.5 }}>
      SUPPORT
    </Typography>
    <Stack spacing={1.5}>
      <Box>
        <Typography sx={{ fontSize: '0.8125rem', fontWeight: 700 }} variant="body2">
          Contact Us:
        </Typography>
        <Link href={`mailto:${PREDICTIVE_SERVICES_EMAIL}`} sx={{ fontSize: '0.8125rem', overflowWrap: 'anywhere' }}>
          {PREDICTIVE_SERVICES_EMAIL}
        </Link>
      </Box>
      <Box>
        <Typography sx={{ fontSize: '0.8125rem', fontWeight: 700 }} variant="body2">
          After Hours Support:
        </Typography>
        <Link href={`mailto:${TECH_SERVICES_EMAIL}`} sx={{ fontSize: '0.8125rem', overflowWrap: 'anywhere' }}>
          {TECH_SERVICES_EMAIL}
        </Link>
      </Box>
    </Stack>
  </Box>
)

export default SupportSection
