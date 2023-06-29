import React from 'react'
import { styled } from '@mui/material/styles'

import IconButton from '@mui/material/IconButton'
import ArrowBackIosIcon from '@mui/icons-material/ArrowBackIos'
import ArrowForwardIosIcon from '@mui/icons-material/ArrowForwardIos'
import CloseIcon from '@mui/icons-material/Close'
import { PARTIAL_WIDTH } from 'utils/constants'

const PREFIX = 'ExpandableContainer'

const classes = {
  root: `${PREFIX}-root`,
  ordering: `${PREFIX}-ordering`,
  expandCollapse: `${PREFIX}-expandCollapse`,
  content: `${PREFIX}-content`
}

const Root = styled('div')<Pick<Props, 'open' | 'currentWidth'>>(({ open, currentWidth }) => ({
  [`& .${classes.root}`]: {
    order: 0,
    width: getRootWidth(open, currentWidth),
    overflowX: 'hidden',
    boxShadow: '0px 3px 3px -2px rgb(0 0 0 / 20%), 0px 3px 4px 0px rgb(0 0 0 / 14%), 0px 1px 8px 0px rgb(0 0 0 / 12%)'
  },
  [`& .${classes.ordering}`]: {
    display: 'flex',
    flexDirection: 'row'
  },
  [`& .${classes.expandCollapse}`]: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center'
  },
  [`& .${classes.content}`]: {
    width: getRootWidth(open, currentWidth),
    position: 'relative'
  }
}))

const getRootWidth = (open: boolean, currentWidth: number) => {
  if (open) {
    return currentWidth > PARTIAL_WIDTH ? '100%' : currentWidth
  }
  return 0
}
interface Props {
  expand: () => void
  collapse: () => void
  close: () => void
  currentWidth: number
  open: boolean
  children: React.ReactNode
}

const ExpandableContainer = (props: Props) => {
  const collapsed = props.currentWidth === PARTIAL_WIDTH
  return (
    <Root className={classes.root} open={props.open} currentWidth={props.currentWidth}>
      <IconButton
        value="close"
        color="primary"
        aria-label="Close side view"
        onClick={() => {
          props.close()
        }}
        size="large"
      >
        <CloseIcon />
      </IconButton>
      <div className={classes.ordering}>
        <div
          className={classes.expandCollapse}
          onClick={() => {
            collapsed || !props.open ? props.expand() : props.collapse()
          }}
        >
          <IconButton
            value="expand-collapse"
            data-testid="expand-collapse-button"
            color="primary"
            aria-label="Expand side view"
            onClick={() => {
              collapsed ? props.expand() : props.collapse()
            }}
            size="large"
          >
            {collapsed ? <ArrowBackIosIcon /> : <ArrowForwardIosIcon />}
          </IconButton>
        </div>
        <div className={classes.content} data-testid="expandable-container-content">
          {props.children}
        </div>
      </div>
    </Root>
  )
}

export default React.memo(ExpandableContainer)
