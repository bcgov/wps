import { Box, styled, Typography, useTheme } from '@mui/material'

const StyledDescription = styled(Typography)(() => ({
  color: 'white',
  textAlign: 'center',
  fontWeight: 'bold'
}))

const AppDescription = () => {
  const theme = useTheme()
  return (
    <Box>
      <StyledDescription data-testid="app-description-p1" variant="body1">
        A spatial analysis tool that automates the continuous monitoring, updating, and communication of anticipated
        fire behaviour that will challenge direct suppression efforts and put the safety of responders at risk.
      </StyledDescription>
      <StyledDescription data-testid="app-description-p2" variant="body1" sx={{ pt: theme.spacing(4) }}>
        A government of BC IDIR is required for advanced features.
      </StyledDescription>
    </Box>
  )
}

export default AppDescription
