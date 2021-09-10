import { makeStyles} from '@material-ui/core'
import React from 'react'
import FixedDecimalNumberCell from './FixedDecimalNumberCell'

interface HFICellProps {
  value: number | undefined
  className?: string
}

const useStyles = makeStyles({
  dataRow: {
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  },
  orangeBorder: {
    border: 'solid 3px #FFC464',
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  },
  orangeFill: {
    backgroundColor: '#FFC464',
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  },
  redFill: {
    backgroundColor: '#FF6259',
    height: '40px',
    paddingLeft: '8px',
    paddingRight: '8px'
  },
})



const DECIMAL_PLACES = 1

const HFICell = (props: HFICellProps) => {
  const classes = useStyles()

  const HFIStyle = getHFIStyle(props.value);

  function getHFIStyle(value:number | undefined): string  {
    if(value !== undefined){
        if(value >= 3000 && value <= 3999){
            return classes.orangeBorder;
        }
        else if(value >= 4000 && value <= 9999){
            return classes.orangeFill;
        }
        else if(value >= 10000){
            return classes.redFill;
        }
    }
    return classes.dataRow;
    
  }

  return(
      <FixedDecimalNumberCell className={HFIStyle} value = {props.value}/>
  )
  
}

export default React.memo(HFICell)
