import { Typography, Box } from '@mui/material'

interface OptionalHeadingProps {
  children: React.ReactNode
}

const OptionalHeading = ({ children }: OptionalHeadingProps) => (
  <Box sx={{ display: 'flex', flexDirection: 'row', alignItems: 'center', pb: 2 }}>
    <Typography variant="body1" sx={{ mr: 1 }}>
      {children}
    </Typography>
    <Typography variant="body2" color="text.secondary">
      [Optional]
    </Typography>
  </Box>
)

export default OptionalHeading
