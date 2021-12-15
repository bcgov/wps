import { makeStyles, Tooltip } from '@material-ui/core'
import InfoOutlinedIcon from '@material-ui/icons/InfoOutlined'
import React from 'react'

const useStyles = makeStyles({
  infoIcon: {
    style: {
      fill: '#1A5A96',
      textAlign: 'center'
    }
  }
})
const FireTypeTooltip = () => {
  const classes = useStyles()

  const typeToolTipFirstLine = 'SUR = Surface Type'
  const typeToolTipSecondLine = 'IC = Intermittent Crown Type'
  const typeToolTipThirdLine = 'CC = Continuous Crown Type'
  const typeToolTipElement = (
    <div>
      {typeToolTipFirstLine} <br />
      {typeToolTipSecondLine} <br />
      {typeToolTipThirdLine}
    </div>
  )

  const tooltipElement = (
    <Tooltip
      title={typeToolTipElement}
      aria-label={`${typeToolTipFirstLine} \n ${typeToolTipSecondLine} \n ${typeToolTipThirdLine}`}
    >
      <InfoOutlinedIcon className={classes.infoIcon}></InfoOutlinedIcon>
    </Tooltip>
  )

  return tooltipElement
}

export default React.memo(FireTypeTooltip)
