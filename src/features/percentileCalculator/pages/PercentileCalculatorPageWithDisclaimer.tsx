import React from 'react'
import { makeStyles } from '@material-ui/core/styles'
import { Modal, Card, Button } from '@material-ui/core'
import InfoIcon from '@material-ui/icons/Info'

import { PercentileCalculatorPage } from 'features/percentileCalculator/pages/PercentileCalculatorPage'

const useStyles = makeStyles({
  cardWrapper: {
    height: '100%',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center'
  },
  card: {
    maxWidth: 600,
    maxHeight: 'calc(100% - 32px)',
    margin: 16,
    overflowY: 'auto',
    padding: 16
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    textAlign: 'center'
  },
  iconWrapper: {
    display: 'flex',
    justifyContent: 'center',
    marginBottom: 10
  },
  acceptBtnWrapper: {
    display: 'flex',
    justifyContent: 'center'
  }
})

interface Props {
  showDisclaimer: boolean
}

export const PercentileCalculatorPageWithDisclaimer = (props: Props) => {
  const classes = useStyles()
  const [show, setShow] = React.useState(props.showDisclaimer)

  const handleClose = () => {
    setShow(false)
  }

  if (!show) {
    return <PercentileCalculatorPage />
  }

  return (
    <Modal open={show} aria-labelledby="disclaimer-modal" onClose={handleClose}>
      <div className={classes.cardWrapper}>
        <Card className={classes.card}>
          <div className={classes.iconWrapper}>
            <InfoIcon color="secondary" fontSize="large" />
          </div>
          <div className={classes.title}>Warranty Disclaimer</div>
          <p>
            This 90th Percentile Forest Fire Weather Index (FWI) system software and
            related documentation is provided as a public service by the Government of
            British Columbia, Box 9411, Victoria, British Columbia, Canada V8W 9V1.
          </p>
          <p>
            This 90th Percentile Forest Fire Weather Index (FWI) system software and
            related documentation are provided &quot;as is&quot; without warranty of any
            kind, whether express or implied. Users of this software and documentation do
            so at their own risk. All implied warranties, including, without limitation,
            implied warranties of merchantability, fitness for a particular purpose, and
            non-infringement, are hereby expressly disclaimed. Links and references to any
            other websites or software are provided for information only and listing shall
            not be taken as endorsement of any kind.
          </p>
          <p>
            The Government of British Columbia is not responsible for the content or
            reliability of any linked software and websites and does not endorse the
            content, products, services or views expressed within them. It is the
            responsibility of all persons who use 90th Percentile Forest Fire Weather
            Index (FWI) system software and related documentation to independently confirm
            the accuracy of the data, information, or results obtained through their use.
          </p>
          <p>
            Limitation of Liabilities Under no circumstances will the Government of
            British Columbia be liable to any person or business entity for any direct,
            indirect, special, incidental, consequential, or other damages based on any
            use of this software and documentation or any other software to which this
            site is linked, including, without limitation, any lost profits, business
            interruption, or loss of programs or information, even if the Government of
            British Columbia has been specifically advised of the possibility of such
            damages.
          </p>
          <div className={classes.acceptBtnWrapper}>
            <Button
              data-testid="disclaimer-accept-button"
              color="primary"
              variant="contained"
              onClick={handleClose}
            >
              Accept
            </Button>
          </div>
        </Card>
      </div>
    </Modal>
  )
}
