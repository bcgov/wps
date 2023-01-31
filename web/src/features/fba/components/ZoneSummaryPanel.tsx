import React from 'react'
import { TextField } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isUndefined } from 'lodash'
import { FireZone } from 'api/fbaAPI'

const useStyles = makeStyles({
  wrapper: {
    minWidth: 300
  }
})

interface Props {
  className?: string
  selectedFireZone: FireZone | undefined
}

const ZoneSummaryPanel = (props: Props) => {
  const classes = useStyles()

  if (isUndefined(props.selectedFireZone)) {
    return <div></div>
  } else {
    return (
      <div className={props.className}>
        <div className={classes.wrapper}>
          <TextField value={props.selectedFireZone.mof_fire_zone_name} />
        </div>
      </div>
    )
  }
}

export default React.memo(ZoneSummaryPanel)
