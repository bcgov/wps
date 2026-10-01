import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import CloseIcon from '@mui/icons-material/Close'
import { Box, Divider, IconButton, Link, Stack, Typography } from '@mui/material'
import { useIsTablet } from '@/hooks/useIsTablet'

interface AboutDataPanelProps {
  onBack: () => void
  onClose: () => void
}

const fuelTypesUrl = 'https://cwfis.cfs.nrcan.gc.ca/en/background/fuel-types?fuel=c1'

export const AboutDataPanel = ({ onBack, onClose }: AboutDataPanelProps) => {
  const isTablet = useIsTablet()

  return (
    <Box
      sx={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 0, width: isTablet ? 460 : '100vw' }}
    >
      <Box
        sx={{
          alignItems: 'center',
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          flexShrink: 0,
          gap: 1,
          px: 1,
          py: 0.5
        }}
      >
        <IconButton aria-label="back to menu" onClick={onBack}>
          <ArrowBackIcon />
        </IconButton>
        <Typography component="h2" sx={{ flexGrow: 1 }} variant="h6">
          About This Data
        </Typography>
        <IconButton aria-label="close about this data" onClick={onClose}>
          <CloseIcon />
        </IconButton>
      </Box>
      <Box sx={{ flex: 1, minHeight: 0, overflowY: 'auto', overscrollBehavior: 'contain' }}>
        <Stack divider={<Divider flexItem />} spacing={2.5} sx={{ maxWidth: 600, mx: 'auto', p: 2.5 }}>
          <Box component="section">
            <Typography component="h3" gutterBottom sx={{ color: 'primary.main', fontWeight: 700 }} variant="subtitle1">
              Fire Behaviour Advisory
            </Typography>
            <Typography variant="body1">
              A Fire Zone is under a Fire Behaviour Advisory if greater than 20% of the combustible land (trees, grass,
              slash) is forecast to have a Head Fire Intensity between 4,000 and 10,000 kW/m.
            </Typography>
          </Box>
          <Box component="section">
            <Typography component="h3" gutterBottom sx={{ color: 'primary.main', fontWeight: 700 }} variant="subtitle1">
              Fire Behaviour Warning
            </Typography>
            <Typography variant="body1">
              A Fire Zone is under a Fire Behaviour Warning if greater than 20% of the combustible land is forecast to
              have a Head Fire Intensity greater than 10,000 kW/m.
            </Typography>
          </Box>
          <Box component="section">
            <Typography component="h3" gutterBottom sx={{ color: 'primary.main', fontWeight: 700 }} variant="subtitle1">
              Fuel types in the text bulletin
            </Typography>
            <Typography variant="body1">
              The{' '}
              <Link
                href={fuelTypesUrl}
                onClick={event => {
                  event.preventDefault()
                  window.open(fuelTypesUrl, '_blank', 'noopener,noreferrer')
                }}
                rel="noopener noreferrer"
                target="_blank"
              >
                fuel types
              </Link>{' '}
              chosen for the text bulletin are the most common fuel types in a zone that meet or exceed the Fire
              Behaviour Advisory threshold of 4,000 kW/m.
            </Typography>
          </Box>
          <Box component="section">
            <Typography component="h3" gutterBottom sx={{ color: 'primary.main', fontWeight: 700 }} variant="subtitle1">
              Portion under advisory
            </Typography>
            <Typography variant="body1">
              For each topographic position, “Portion under advisory” shows the percentage of it's combustible area
              within the Fire Zone with Head Fire Intensity of at least 4,000 kW/m. Each position’s percentage is
              calculated separately.
            </Typography>
          </Box>
        </Stack>
      </Box>
    </Box>
  )
}
