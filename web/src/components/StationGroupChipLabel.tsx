import { Box, Typography } from '@mui/material'
import { theme } from 'app/theme'
import React from 'react'

interface StationGroupChipProps {
  idir: string
  groupName: string
}

const StationGroupChipLabel = ({ idir, groupName }: StationGroupChipProps) => {
  return (
    <Box>
      <Box
        sx={{
          margin: 0,
          padding: 0,
          marginTop: 0.5,
          border: 1,
          borderRadius: '5%',
          borderColor: theme.palette.grey[500]
        }}
      >
        <Typography paragraph variant="caption" sx={{ padding: 0, margin: 0, color: theme.palette.grey[500] }}>
          {idir}
        </Typography>
      </Box>
      <Typography paragraph variant="body2" sx={{ padding: 0, margin: 0 }}>
        {groupName}
      </Typography>
    </Box>
  )
}

export default React.memo(StationGroupChipLabel)
