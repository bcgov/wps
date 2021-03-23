import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

const sidePanelWidth = 850

const useStyles = makeStyles({
  root: (props: Props) => ({
    order: 2,
    width: props.show ? sidePanelWidth : 0,
    overflowX: 'hidden',
    transition: '0.4s',
    boxShadow:
      '0px 3px 3px -2px rgb(0 0 0 / 20%), 0px 3px 4px 0px rgb(0 0 0 / 14%), 0px 1px 8px 0px rgb(0 0 0 / 12%)'
  }),
  content: {
    width: sidePanelWidth,
    padding: 12,
    paddingTop: 22,
    position: 'relative'
  },
  closeBtn: {
    position: 'absolute',
    top: 0,
    left: 10,
    fontSize: 28,
    cursor: 'pointer',
    fontWeight: 'bold'
  }
})

interface Props {
  show: boolean
  closeSidePanel: () => void
  children: React.ReactNode
}

const SidePanel = (props: Props) => {
  const classes = useStyles(props)

  return (
    <div className={classes.root}>
      <div className={classes.content}>
        <div className={classes.closeBtn} onClick={props.closeSidePanel} role="button">
          &times;
        </div>
        {props.children}
      </div>
    </div>
  )
}

export default React.memo(SidePanel)
