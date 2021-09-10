import { makeStyles, TableCell } from '@material-ui/core'
import React from 'react'

interface HFICellProps {
  value: number | undefined
  className?: string
}

const useStyles = makeStyles({
  dataRow: {
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  }
})

const DECIMAL_PLACES = 1

const HFICell = (props: HFICellProps) => {
  const classes = useStyles()

  if (props.value !== undefined) {
    if (props.value >= 3000 && props.value <= 3999) {
        return (
            <TableCell style={{border: 'solid 1px #FFC464'}} className={props.className ? props.className : classes.dataRow}>
              {props.value?.toFixed(DECIMAL_PLACES)}
            </TableCell>
          )
    }
    else if(props.value >= 4000){
        return (
            <TableCell style={{backgroundColor: '#FFC464'}} className={props.className ? props.className : classes.dataRow}>
              {props.value?.toFixed(DECIMAL_PLACES)}
            </TableCell>
          )
    }
    else if(props.value >= 10000){
        return (
            <TableCell style={{backgroundColor: '#FF6259'}} className={props.className ? props.className : classes.dataRow}>
              {props.value?.toFixed(DECIMAL_PLACES)}
            </TableCell>
          )
    }
  }

  return (
    <TableCell className={props.className ? props.className : classes.dataRow}>
      {props.value}
    </TableCell>
  )

  
}

export default React.memo(HFICell)
