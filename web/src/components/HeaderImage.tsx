import React from 'react'
import makeStyles from '@mui/styles/makeStyles'

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
    <a href="https://psu.nrs.gov.bc.ca/">
      <img className={classes.logo} src={'/images/BCID_H_rgb_rev.svg'} alt="B.C. Government logo" />
    </a>
  )
}

export default React.memo(ImageHeader)
