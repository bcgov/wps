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
    width: props.show ? props.currentWidth : 0,
    overflowX: 'hidden',
    boxShadow:
      '0px 3px 3px -2px rgb(0 0 0 / 20%), 0px 3px 4px 0px rgb(0 0 0 / 14%), 0px 1px 8px 0px rgb(0 0 0 / 12%)'
  }),
  content: (props: Props) => ({
    width: props.currentWidth,
    position: 'relative'
  }),
  actions: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'flex-start'
  }
})

interface Props {
  expandSidePanel: () => void
  collapseSidePanel: () => void
  closeSidePanel: () => void
  currentWidth: number
  show: boolean
  children: React.ReactNode
}

export const ExpandableContainer = (props: Props) => {
  const classes = useStyles(props)
  const closeButton = (
    <IconButton
      color="primary"
      aria-label="Close side view"
      onClick={props.closeSidePanel}
    >
      <CloseIcon />
    </IconButton>
  )
  return props.currentWidth === partialWidth ? (
    <div className={classes.root}>
      <div className={classes.content}>
        <div className={classes.actions}>
          <React.Fragment>
            {closeButton}
            <IconButton
              color="primary"
              aria-label="Expand side view"
              onClick={props.expandSidePanel}
            >
              <ArrowBackIosIcon />
            </IconButton>
          </React.Fragment>
        </div>
        {props.children}
      </div>
    </div>
  ) : (
    <div className={classes.root}>
      <div className={classes.content}>
        <div className={classes.actions}>
          <React.Fragment>
            {closeButton}
            <IconButton
              color="primary"
              aria-label="Collapse side view"
              onClick={props.collapseSidePanel}
            >
              <ArrowForwardIosIcon />
            </IconButton>
          </React.Fragment>
        </div>
        {props.children}
      </div>
    </div>
  )
}
