import React from 'react'
import { styled } from '@mui/material/styles'
import { ToggleButton, ToggleButtonGroup } from '@mui/material'

const PREFIX = 'SidePanel'

const classes = {
  root: `${PREFIX}-root`,
  content: `${PREFIX}-content`,
  actions: `${PREFIX}-actions`,
  closeBtn: `${PREFIX}-closeBtn`
}

const Root = styled('div')({
  [`&.${classes.root}`]: {
    order: 2,
    overflowX: 'hidden'
  },
  [`& .${classes.content}`]: {
    position: 'relative'
  },
  [`& .${classes.actions}`]: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'flex-start'
  },
  [`& .${classes.closeBtn}`]: {
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
  handleToggleView: (_: React.MouseEvent<HTMLElement>, newDataView: SidePanelEnum) => void
  showTableView: string
  stationCodes: number[]
  children: React.ReactNode
}

const SidePanel = (props: Props) => {
  return (
    <Root className={classes.root} data-testid="sidepanel">
      <div className={classes.content}>
        <div className={classes.actions}>
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
            {props.stationCodes.length > 1 && (
              <ToggleButton value={SidePanelEnum.Comparison} data-testid="station-comparison-button">
                Station comparison
              </ToggleButton>
            )}
          </ToggleButtonGroup>
        </div>
        {props.children}
      </div>
    </Root>
  )
}

export default React.memo(SidePanel)
