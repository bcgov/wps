import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { ToggleButton, ToggleButtonGroup } from '@material-ui/lab'

const useStyles = makeStyles({
  root: {
    order: 2,
    overflowX: 'hidden'
  },
  content: {
    position: 'relative'
  },
  actions: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'flex-start'
  },
  closeBtn: {
    marginRight: 10,
    fontSize: 28,
    cursor: 'pointer',
    fontWeight: 'bold'
  }
})

interface Props {
  handleToggleView: (_: React.MouseEvent<HTMLElement>, newDataView: string) => void
  showTableView: string
  children: React.ReactNode
}

const SidePanel = (props: Props) => {
  const classes = useStyles(props)

  return (
    <div className={classes.root} data-testid="sidepanel">
      <div className={classes.content}>
        <div className={classes.actions}>
          <ToggleButtonGroup
            color="primary"
            aria-label="outlined primary button group"
            value={props.showTableView}
            onChange={props.handleToggleView}
            size="small"
          >
            <ToggleButton value="true">Tables</ToggleButton>
            <ToggleButton value="false">Graphs</ToggleButton>
          </ToggleButtonGroup>
        </div>
        {props.children}
      </div>
    </div>
  )
}

export default React.memo(SidePanel)
