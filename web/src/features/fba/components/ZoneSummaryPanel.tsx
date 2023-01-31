import React from 'react'
import { TextField } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { isNull } from 'lodash'

const useStyles = makeStyles({
  wrapper: {
    minWidth: 300
  }
})

interface Props {
  className?: string
  selectedZoneID: number | null
}

const ZoneSummaryPanel = (props: Props) => {
  const classes = useStyles()

  if (isNull(props.selectedZoneID)) {
    return <div></div>
  } else {
    return (
      <div className={props.className}>
        <div className={classes.wrapper}>
          <TextField value={props.selectedZoneID} />
        </div>
      </div>
    )
  }
}

export default React.memo(ZoneSummaryPanel)
