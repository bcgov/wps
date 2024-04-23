import React from 'react'
import { styled } from '@mui/material/styles'
import FeedbackButton from 'components/FeedbackButton'
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
  console.log(productName)
  return (
    <Root>
      <FeedbackButton color="inherit" />
    </Root>
  )
}

export default React.memo(Contact)
