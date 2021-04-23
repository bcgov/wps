import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

import IconButton from '@material-ui/core/IconButton'
import ArrowBackIosIcon from '@material-ui/icons/ArrowBackIos'
import ArrowForwardIosIcon from '@material-ui/icons/ArrowForwardIos'
import CloseIcon from '@material-ui/icons/Close'

export const partialWidth = 850

const useStyles = makeStyles({
  root: (props: Props) => ({
    order: 2,
    width: props.open ? props.currentWidth : 0,
    overflowX: 'hidden',
    boxShadow:
      '0px 3px 3px -2px rgb(0 0 0 / 20%), 0px 3px 4px 0px rgb(0 0 0 / 14%), 0px 1px 8px 0px rgb(0 0 0 / 12%)'
  }),
  ordering: {
    display: 'flex',
    flexDirection: 'row'
  },
  expandCollapse: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center'
  },
  close: {
    display: 'flex',
    flexDirection: 'column'
  },
  content: (props: Props) => ({
    width: props.currentWidth,
    position: 'relative'
  })
})

interface Props {
  expand: () => void
  collapse: () => void
  close: () => void
  currentWidth: number
  open: boolean
  children: React.ReactNode
}

export const ExpandableContainer = (props: Props) => {
  const classes = useStyles(props)
  const collapsed = props.currentWidth === partialWidth
  return (
    <div className={classes.root}>
      <IconButton color="primary" aria-label="Close side view" onClick={props.close}>
        <CloseIcon />
      </IconButton>
      <div className={classes.ordering}>
        <div className={classes.expandCollapse}>
          <div className={classes.close}></div>
          <IconButton
            color="primary"
            aria-label="Expand side view"
            onClick={collapsed ? props.expand : props.collapse}
          >
            {collapsed ? <ArrowBackIosIcon /> : <ArrowForwardIosIcon />}
          </IconButton>
        </div>
        <div className={classes.content}>{props.children}</div>
      </div>
    </div>
  )
}
