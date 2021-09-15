import { makeStyles } from '@material-ui/core'
import React from 'react'

interface FireDisplayContainerProps {
  children?: React.ReactNode
  testId?: string
}
const useStyles = makeStyles(() => ({
  display: {
    paddingBottom: 12,

    '& .MuiTableCell-sizeSmall': {
      padding: '6px 6px 6px 6px',
      height: '40px'
    },

    '& .MuiTableCell-stickyHeader': {
      padding: '8px'
    },

    '& .MuiInputBase-root': {
      fontSize: '1em'
    },

    '& .MuiOutlinedInput-root': {
      padding: '0'
    },
    '& .MuiTableCell-head': { fontWeight: 'bold', padding: '1px', paddingLeft: '7px' }
  }
}))

const FireDisplayContainer = (props: FireDisplayContainerProps) => {
  const classes = useStyles()

  return (
    <div className={classes.display} data-testid={props.testId}>
      {props.children}
    </div>
  )
}

export default React.memo(FireDisplayContainer)
