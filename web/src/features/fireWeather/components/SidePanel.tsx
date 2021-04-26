import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { ToggleButton, ToggleButtonGroup } from '@material-ui/lab'

const sidePanelWidth = 850

const useStyles = makeStyles({
  root: (props: Props) => ({
    order: 2,
    width: props.show ? sidePanelWidth : 0,
    overflowX: 'hidden',
    boxShadow:
      '0px 3px 3px -2px rgb(0 0 0 / 20%), 0px 3px 4px 0px rgb(0 0 0 / 14%), 0px 1px 8px 0px rgb(0 0 0 / 12%)'
  }),
  content: {
    width: sidePanelWidth,
    padding: '22px 24px 12px 12px',
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

export enum SidePanelEnum {
  Tables = 'tables',
  Graphs = 'graphs',
  Comparison = 'comparison'
}

interface Props {
  show: boolean
  closeSidePanel: () => void
  handleToggleView: (_: React.MouseEvent<HTMLElement>, newDataView: SidePanelEnum) => void
  showTableView: string
  children: React.ReactNode
}

const SidePanel = (props: Props) => {
  const classes = useStyles(props)

  return (
    <div className={classes.root}>
      <div className={classes.content}>
        <div className={classes.actions}>
          <div className={classes.closeBtn} onClick={props.closeSidePanel} role="button">
            &times;
          </div>
          <ToggleButtonGroup
            exclusive={true}
            color="primary"
            aria-label="outlined primary button group"
            value={props.showTableView}
            onChange={props.handleToggleView}
            size="small"
          >
            <ToggleButton value={SidePanelEnum.Tables}>Tables</ToggleButton>
            <ToggleButton value={SidePanelEnum.Graphs}>Graphs</ToggleButton>
            <ToggleButton value={SidePanelEnum.Comparison}>
              Station comparison
            </ToggleButton>
          </ToggleButtonGroup>
        </div>
        {props.children}
      </div>
    </div>
  )
}

export default React.memo(SidePanel)
