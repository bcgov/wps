import Box from '@mui/material/Box'
import type { ReactNode } from 'react'

const ICON_TILE_RADIUS = '14px'

interface ToolIconTileProps {
  icon: ReactNode
  iconScale?: number
  size?: number
}

const ToolIconTile = ({ icon, iconScale = 1, size = 48 }: ToolIconTileProps) => (
  <Box
    sx={{
      alignItems: 'center',
      bgcolor: 'grey.50',
      borderRadius: ICON_TILE_RADIUS,
      display: 'flex',
      flex: '0 0 auto',
      height: size,
      justifyContent: 'center',
      overflow: 'hidden',
      width: size
    }}
  >
    <Box sx={{ display: 'flex', transform: `scale(${iconScale})` }}>{icon}</Box>
  </Box>
)

export default ToolIconTile
