import React from 'react'
import { styled } from '@mui/material/styles'
import Container from '@mui/material/Container'
import Grid from '@mui/material/Grid'
import { Typography } from '@mui/material'
import ToolCard from 'features/landingPage/components/ToolCard'
import { toolInfos } from 'features/landingPage/toolInfo'

const PREFIX = 'ToolCardsPage'

const classes = {
  grid: `${PREFIX}-grid`,
  title: `${PREFIX}-title`
}

const StyledContainer = styled(Container)(({ theme }) => ({
  [`& .${classes.grid}`]: {
    paddingBottom: theme.spacing(2)
  },

  [`& .${classes.title}`]: {
    fontSize: '2rem',
    fontWeight: 700,
    paddingBottom: theme.spacing(1),
    paddingTop: theme.spacing(1)
  }
}))

const ToolCardsPage: React.FunctionComponent = () => {
  return (
    <StyledContainer>
      <Typography className={classes.title}>Decision Support Tools</Typography>
      <Grid className={classes.grid} container spacing={2.5}>
        {toolInfos.map(item => {
          return (
            <Grid style={{ display: 'flex' }} key={item.name} item sm={12} md={6} lg={4}>
              <ToolCard
                description={item.description}
                icon={item.icon}
                isBeta={item.isBeta}
                route={item.route}
                name={item.name}
              />
            </Grid>
          )
        })}
      </Grid>
    </StyledContainer>
  )
}

export default ToolCardsPage
