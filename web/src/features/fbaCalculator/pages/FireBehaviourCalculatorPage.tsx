import { Paper } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import { Container, GeneralHeader } from 'components'
import React from 'react'
import FBATable from 'features/fbaCalculator/components/FBATable'

export const FireBehaviourCalculator: React.FunctionComponent = () => {
  const useStyles = makeStyles(theme => ({
    disclaimer: {
      borderLeft: '6px solid #FCBA19',
      padding: '10px',
      marginBottom: theme.spacing(8),
      marginTop: '24px'
    },
    content: {
      display: 'flex',
      flexDirection: 'row'
    }
  }))

  const classes = useStyles()
  return (
    <main>
      <GeneralHeader spacing={1} title="Predictive Services Unit" productName="Predictive Services Unit" />
      <Container maxWidth={'xl'}>
        <h1>
          {/* (🔥🦇) */}
          Fire Behaviour Advisory Tool
        </h1>
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
    </main>
  )
}
