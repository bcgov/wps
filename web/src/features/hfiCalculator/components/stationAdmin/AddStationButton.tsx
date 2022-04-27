import React from 'react'
import { Button } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline'
import { theme } from 'app/theme'

export interface AddStationProps {
  clickHandler: () => void
}

const useStyles = makeStyles(() => ({
  addStation: {
    margin: theme.spacing(1),
    float: 'right'
  }
}))
const AddStationButton = (props: AddStationProps) => {
  const classes = useStyles()
  return (
    <Button
      variant="text"
      color="primary"
      className={classes.addStation}
      onClick={props.clickHandler}
      data-testid={'add-station-button'}
    >
      <AddCircleOutlineIcon />
      Add weather station
    </Button>
  )
}

export default React.memo(AddStationButton)
