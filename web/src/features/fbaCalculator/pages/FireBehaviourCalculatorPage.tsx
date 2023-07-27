import React, { useEffect } from 'react'
import { styled } from '@mui/material/styles'
import { Paper } from '@mui/material'
import { Container, GeneralHeader } from 'components'
import FBATable from 'features/fbaCalculator/components/FBATable'
import { FIREBAT_DOC_TITLE } from 'utils/constants'

const PREFIX = 'FireBehaviourCalculator'

const classes = {
  disclaimer: `${PREFIX}-disclaimer`,
  content: `${PREFIX}-content`
}

const Root = styled('main')(({ theme }) => ({
  [`& .${classes.disclaimer}`]: {
    borderLeft: '6px solid #FCBA19',
    padding: '10px',
    marginBottom: theme.spacing(8),
    marginTop: '24px'
  },

  [`& .${classes.content}`]: {
    display: 'flex',
    flexDirection: 'row'
  }
}))

const FireBehaviourCalculator: React.FunctionComponent = () => {
  useEffect(() => {
    document.title = FIREBAT_DOC_TITLE
  }, [])

  return (
    <Root>
      <GeneralHeader
        isBeta={false}
        spacing={1}
        title="Fire Behaviour Advisory Tool"
        productName="Fire Behaviour Advisory Tool"
      />
      <Container sx={{ paddingTop: '0.5em' }} maxWidth={'xl'}>
        <FBATable />
        <Paper className={classes.disclaimer}>
          <div>
            <h4>Disclaimers:</h4>
            <p>
              Forecasted weather outputs are for 13:00 and FWI Indices are for 17:00 PDT. These fire behaviour
              calculations assume flat terrain.
            </p>
            <p>Weather and fire behaviour indices are sourced from the Wildfire One API.</p>
            <p>
              Values are calculated using the{' '}
              <a target="_blank" rel="noopener noreferrer" href="https://r-forge.r-project.org/projects/cffdrs/">
                Canadian Forest Fire Danger Rating System R Library
              </a>{' '}
              and are intended to provide general guidance for Fire Behaviour Advisories.
            </p>
            <p>
              Constants for crown fuel load are taken from &quot;Development and Structure of the Canadian Forest Fire
              Behaviour Prediction System&quot; from Forestry Canada Fire Danger Group, Information Report ST-X-3, 1992.
            </p>
            <p>
              If you have any questions about how values are calculated, please{' '}
              <a href="mailto: bcws.predictiveservices@gov.bc.ca?subject=Predictive Services Unit - Fire Behaviour Advisory Calculator">
                contact us.
              </a>
            </p>
          </div>
        </Paper>
      </Container>
    </Root>
  )
}
export default FireBehaviourCalculator
