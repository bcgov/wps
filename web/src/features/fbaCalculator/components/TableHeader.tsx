import { makeStyles } from '@material-ui/core'
import React from 'react'

interface TableHeaderProps {
  text: string
  maxWidth?: string
}

const TableHeader = (props: TableHeaderProps) => {
  const useStyles = makeStyles({
    header: {
      maxWidth: '80px',
      overflow: 'hidden',
      whiteSpace: 'nowrap',
      textOverflow: 'ellipsis',
      '& span': {
        display: 'none'
      },
      '&:hover span': {
        display: 'block',
        backgroundColor: '#4f4f4f',
        opacity: '0.8',
        paddingLeft: '5px',
        paddingRight: '5px',
        maxWidth: '225px',
        color: '#fff',
        textAlign: 'center',
        borderRadius: '6px',
        /* Position the tooltip */
        position: 'absolute',
        left: '2px',
        top: '41px'
      }
    }
  })

  const classes = useStyles()
  return (
    <div style={{ maxWidth: props.maxWidth }} className={classes.header}>
      {props.text}
      <span>{props.text}</span>
    </div>
  )
}

export default React.memo(TableHeader)
