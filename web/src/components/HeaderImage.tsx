import React from 'react'
import { makeStyles } from '@material-ui/core/styles'

const useStyles = makeStyles({
  logo: {
    width: 175,
    marginTop: '10px',
    marginBottom: '10px'
  }
})

const ImageHeader = () => {
  const classes = useStyles()

  return (
    <a href="https://gov.bc.ca">
      <img
        className={classes.logo}
        src={'/images/BCID_H_rgb_rev.svg'}
        alt="B.C. Government logo"
      />
    </a>
  )
}

export default React.memo(ImageHeader)
