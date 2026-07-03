import { styled } from '@mui/material/styles'
import React from 'react'

const PREFIX = 'HeaderImage'

const classes = {
  logo: `${PREFIX}-logo`
}

const Root = styled('a')({
  [`& .${classes.logo}`]: {
    width: 175,
    marginTop: '10px',
    marginBottom: '10px'
  }
})

const ImageHeader = () => {
  return (
    <Root href="https://psu.nrs.gov.bc.ca/">
      <img className={classes.logo} src={'/images/BCID_H_rgb_rev.svg'} alt="B.C. Government logo" />
    </Root>
  )
}

export default React.memo(ImageHeader)
