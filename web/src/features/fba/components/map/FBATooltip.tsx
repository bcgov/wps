import { Box, CircularProgress } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import React from 'react'

export interface FBATooltipProps {
  testId?: string
  valueAtCoordinate?: number
  loading: boolean
}

const FBATooltip = React.forwardRef((props: FBATooltipProps, ref) => {
  const useStyles = makeStyles({
    popup: {
      position: 'absolute',
      backgroundColor: 'white',
      boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
      padding: 15,
      borderRadius: 10,
      border: '1px solid #cccccc',
      bottom: 12,
      left: -50
    },
    popupCloser: {
      textDecoration: 'none',
      position: 'absolute',
      top: 2,
      right: 8,
      '&::after': {
        content: '✖'
      }
    }
  })

  const classes = useStyles()

  return (
    <Box ref={ref} className={classes.popup}>
      {props.loading ? (
        <CircularProgress />
      ) : (
        <div id="popup-content">
          <p>{`HFI: ${props.valueAtCoordinate}`}</p>
        </div>
      )}
    </Box>
  )
})

FBATooltip.displayName = 'FBATooltip'

export default React.memo(FBATooltip)
