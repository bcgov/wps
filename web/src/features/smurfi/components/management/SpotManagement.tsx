import SMURFIMap from "@/features/smurfi/components/map/SMURFIMap"
import SpotAdmin from "@/features/smurfi/components/management/SpotAdmin"
import { Box } from "@mui/material"

  
const SpotManagement = () => {

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
      <Box sx={{ height: "100%", display: 'flex', flex: 1, flexDirection: 'row', minHeight: 0 }}>
        <Box sx={{ flex: 1 }}>
          <Box sx={{display: "flex", flexGrow: 1}}>
            <SpotAdmin />
          </Box>
        </Box>
        <Box sx={{ height: "100%", flex: 1, position: 'relative', minHeight: 0 }}>
          <SMURFIMap />
        </Box>
      </Box>
    </Box>
  )

}

export default SpotManagement
  
