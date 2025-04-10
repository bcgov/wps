import React, { useEffect } from 'react'
import { styled } from '@mui/material/styles'
import { Container, GeneralHeader } from 'components'
import FBATable from 'features/fbaCalculator/components/FBATable'
import { FIRECALC_DOC_TITLE } from 'utils/constants'

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
    document.title = FIRECALC_DOC_TITLE
  }, [])

  return (
    <Root>
      <GeneralHeader isBeta={false} spacing={1} title="Fire Behaviour Calculator" />
      <Container sx={{ paddingTop: '0.5em' }} maxWidth={'xl'}>
        <FBATable />
      </Container>
    </Root>
  )
}
export default FireBehaviourCalculator
