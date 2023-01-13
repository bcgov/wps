import React from 'react'
import Container from '@mui/material/Container'
import Grid from '@mui/material/Grid'
import ToolCard from 'landingPage/ToolCard'
import { toolInfos } from 'landingPage/toolInfo'

const ToolCards: React.FunctionComponent = () => {
  return (
    <Container>
      <Grid container spacing={2.5}>
        {toolInfos.map(item => {
          return (
            <Grid style={{ display: 'flex' }} key={item.name} item sm={12} md={6} lg={4}>
              <ToolCard description={item.description} icon={item.icon} route={item.route} name={item.name} />
            </Grid>
          )
        })}
      </Grid>
    </Container>
  )
}

export default ToolCards
