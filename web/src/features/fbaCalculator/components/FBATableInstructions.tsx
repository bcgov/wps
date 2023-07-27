import { styled } from '@mui/material/styles'
import React from 'react'

const PREFIX = 'FBATableInstructions'

const classes = {
  content: `${PREFIX}-content`
}

const Root = styled('div')({
  [`&.${classes.content}`]: {
    marginLeft: '2em',
    textAlign: 'left'
  }
})

const FBATableInstructions = () => {
  return (
    <Root data-testid={'fba-instructions'} className={classes.content}>
      <p>Add a row to get started.</p>
      <p>
        Build custom lists of weather stations by fire center, zone or fuel type. Bookmark the URL to save your custom
        list.
      </p>
    </Root>
  )
}

export default React.memo(FBATableInstructions)
