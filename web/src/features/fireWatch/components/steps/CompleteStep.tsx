import { FORM_MAX_WIDTH } from "@/features/fireWatch/components/CreateFireWatch"
import { Box, Step, Typography, useTheme } from "@mui/material"

const CompleteStep = () => {
  const theme = useTheme()

  return (
    <Step>
      <Box sx={{display: 'flex', flexDirection: 'column', maxWidth: `${FORM_MAX_WIDTH}px`, padding: theme.spacing(4)}}>
        <Typography sx={{fontWeight: "bold"}} variant='body1'>
          A new fire watch has been successfully submitted. You will receive a notification at the provided email each time the burn comes into prescription.
        </Typography>
      </Box>
    </Step>
  )
}

export default CompleteStep