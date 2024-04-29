import React from 'react'
import { styled } from '@mui/material/styles'
const PREFIX = 'Contact'

const classes = {
  contact: `${PREFIX}-contact`,
  plainText: `${PREFIX}-plainText`
}

const Root = styled('div')({
  [`& .${classes.contact}`]: {
    color: 'white',
    fontStyle: 'bold',
    fontSize: '1.1em',
    textDecoration: 'underline',
    cursor: 'pointer'
  },
  [`& .${classes.plainText}`]: {
    color: 'white',
    fontStyle: 'bold',
    fontSize: '1.1em'
  }
})

interface Props {
  productName: string
}

const Contact = (props: Props) => {
  const productName = props.productName

  return (
    <Root>
      <a className={classes.plainText}>Email: </a>
      <a
        id="contact-link"
        className={classes.contact}
        href={`mailto:bcws.predictiveservices@gov.bc.ca?subject=Predictive Services Unit - ${productName}`}
      >
        bcws.predictiveservices@gov.bc.ca
      </a>
    </Root>
  )
}

export default React.memo(Contact)
