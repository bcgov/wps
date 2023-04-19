import React from 'react'
import makeStyles from '@mui/styles/makeStyles'

const useStyles = makeStyles({
  contact: {
    color: 'white',
    fontStyle: 'bold',
    fontSize: '1.1em',
    textDecoration: 'underline',
    cursor: 'pointer'
  },
  plainText: {
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

  const classes = useStyles()

  return (
    <div>
      <a className={classes.plainText}>Email: </a>
      <a
        id="contact-link"
        className={classes.contact}
        href={`mailto:bcws.predictiveservices@gov.bc.ca?subject=Predictive Services Unit - ${productName}`}
      >
        bcws.predictiveservices@gov.bc.ca
      </a>
    </div>
  )
}

export default React.memo(Contact)
