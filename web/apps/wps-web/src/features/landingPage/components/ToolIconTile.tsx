import Box from '@mui/material/Box'
import type { ReactNode } from 'react'
import { ICON_TILE_RADIUS } from '../landingPageConfig'

interface ToolIconTileProps {
  icon: ReactNode
  size?: number
}

const ToolIconTile = ({ icon, size = 48 }: ToolIconTileProps) => (
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
    {icon}
  </Box>
)

export default ToolIconTile
