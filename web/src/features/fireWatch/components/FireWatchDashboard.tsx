import { Box, Typography, useTheme } from "@mui/material"


const FireWatchDashboard = () => {
  const theme = useTheme()
  return (
  <Box id='fire-watch-dashboard' sx={{ flexGrow: 1}}>
    <Typography sx={{padding: theme.spacing(2)}} variant='h4'>
      Dashboard
    </Typography>
    <Typography sx={{padding: theme.spacing(3)}} variant='body1'>
      Under construction
    </Typography>   
  </Box>
  )
}

export default FireWatchDashboard