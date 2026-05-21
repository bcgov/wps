import { Box } from '@mui/material'
import { useParams } from 'react-router-dom'

// Display a read only view of the SpotRequest identified by params.id which is taken from the URL
const SpotRequest = () => {
  const params = useParams()
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
      Placeholder for SpotRequest detail: {params.id}
    </Box>
  )
}

export default SpotRequest
