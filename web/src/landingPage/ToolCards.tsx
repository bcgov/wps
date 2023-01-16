import React from 'react'
import Container from '@mui/material/Container'
import Grid from '@mui/material/Grid'
import ToolCard from 'landingPage/ToolCard'
import { toolInfos } from 'landingPage/toolInfo'
import { Typography } from '@mui/material'
import makeStyles from '@mui/styles/makeStyles'

const useStyles = makeStyles(theme => ({
  title: {
    fontSize: '2rem',
    fontWeight: 700,
    paddingBottom: theme.spacing(1),
    paddingTop: theme.spacing(1)
  }
}))

const ToolCards: React.FunctionComponent = () => {
  const classes = useStyles()

  return (
    <Container>
      <Typography className={classes.title}>Decision Support Tools</Typography>
      <Grid container spacing={2.5}>
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

export default ToolCards
