import { makeStyles } from '@material-ui/core'
import React from 'react'

const useStyles = makeStyles({
  content: {
    textAlign: 'center'
  }
})

const FBATableInstructions = () => {
  const classes = useStyles()
  return (
    <div data-testid={'fba-instructions'} className={classes.content}>
      <p>Add a row to get started</p>
      <p>
        Build custom lists of weather stations by fire center, zone or fuel type. Bookmark
        the URL to save your custom list.
      </p>
    </div>
  )
}

export default React.memo(FBATableInstructions)
