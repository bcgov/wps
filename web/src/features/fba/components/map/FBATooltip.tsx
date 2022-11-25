import { Coordinate } from 'ol/coordinate'
import CloseIcon from '@mui/icons-material/Close'
import { Box, CircularProgress, IconButton } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import React, { useEffect } from 'react'
import { IValueAtCoordinate } from 'features/fba/slices/valueAtCoordinateSlice'

export interface FBATooltipProps {
  testId?: string
  valuesAtCoordinate: IValueAtCoordinate[]
  loading: boolean
  onClose: React.Dispatch<React.SetStateAction<Coordinate | undefined>>
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
      right: 2
    }
  })

  const classes = useStyles()

  useEffect(() => {
    const handleEscKey = (e: KeyboardEvent) => {
      if (e.code === 'Escape') props.onClose(undefined)
    }
    document.addEventListener('keydown', handleEscKey)
    return () => document.removeEventListener('keydown', handleEscKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <Box ref={ref} className={classes.popup}>
      {props.loading ? (
        <CircularProgress />
      ) : (
        <div id="popup-content">
          <IconButton className={classes.popupCloser} onClick={() => props.onClose(undefined)} size="small">
            <CloseIcon />
          </IconButton>
          {props.valuesAtCoordinate.map(valueAtCoordinate => {
            return (
              <p key={valueAtCoordinate.description}>
                {valueAtCoordinate.description} :{' '}
                {valueAtCoordinate.value === undefined ? 'undefined' : valueAtCoordinate.value}
              </p>
            )
          })}
        </div>
      )}
    </Box>
  )
})

FBATooltip.displayName = 'FBATooltip'

export default React.memo(FBATooltip)
