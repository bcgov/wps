import { Box } from '@mui/material'
import React, { forwardRef } from 'react'

const ScalebarContainer = forwardRef((_, ref) => {
  return (
    <Box
      data-testid="scalebar-container"
      sx={{
        backgroundColor: '#FFFFFF',
        border: '1px solid #000000',
        padding: '12px',
        position: 'absolute',
        right: '10px',
        bottom: '10px',
        overflow: 'hidden',
        zIndex: 1
      }}
    >
      <Box
        ref={ref}
        sx={{
          ['& div.ol-scale-bar']: {
            position: 'static'
          },
          ['& div.ol-scale-bar-inner div.ol-scale-step-marker']: {
            top: '13px !important'
          },
          ['& div.ol-scale-bar-inner div>div.ol-scale-step-marker']: {
            top: '-8px !important'
          },
          ['& div.ol-scale-step-text']: {
            bottom: '5px !important'
          }
        }}
      ></Box>
    </Box>
  )
})
ScalebarContainer.displayName = 'ScalebarContainer'

export default React.memo(ScalebarContainer)
