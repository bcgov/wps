import React from 'react'
import Container from '@mui/material/Container'
import Grid from '@mui/material/Grid'
import { Typography } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'
import ToolCard from 'features/landingPage/components/ToolCard'
import { toolInfos } from 'features/landingPage/toolInfo'

const useStyles = makeStyles(theme => ({
  grid: {
    paddingBottom: theme.spacing(2)
  },
  title: {
    fontSize: '2rem',
    fontWeight: 700,
    paddingBottom: theme.spacing(1),
    paddingTop: theme.spacing(1)
  }
}))

const ToolCardsPage: React.FunctionComponent = () => {
  const classes = useStyles()

  return (
    <Container>
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
    </Container>
  )
}

export default ToolCardsPage
