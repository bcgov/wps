import React from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Card from '@mui/material/Card'
import CardActions from '@mui/material/CardActions'
import CardContent from '@mui/material/CardContent'
import CardHeader from '@mui/material/CardHeader'
import Typography from '@mui/material/Typography'
import makeStyles from '@mui/styles/makeStyles'
import { Link } from 'react-router-dom'
import BetaTag from 'landingPage/BetaTag'

interface ToolCardProps {
  description: React.ReactNode | string
  icon: React.ReactNode
  isBeta: boolean
  name: string
  route: string
}

const useStyles = makeStyles(theme => ({
  button: {
    height: '2.5rem',
    width: '11.5rem'
  },
  card: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    maxWidth: '400px',
    paddingBottom: theme.spacing(1)
  },
  cardActions: {
    display: 'flex',
    justifyContent: 'center'
  },
  cardContent: {
    alignItems: 'center',
    display: 'flex',
    flexDirection: 'column',
    flexGrow: 1,
    paddingBottom: theme.spacing(1),
    paddingLeft: theme.spacing(3),
    paddingRight: theme.spacing(3),
    paddingTop: 0
  },
  cardDescription: {
    paddingTop: '1rem'
  },
  cardHeader: {
    color: theme.palette.primary.main,
    textAlign: 'center',
    textDecoration: 'underline'
  },
  iconContainer: {
    alignItems: 'center',
    borderColor: '#D9D9D9',
    borderRadius: '50%',
    borderStyle: 'solid',
    borderWidth: '1px',
    display: 'flex',
    height: '7.5rem',
    justifyContent: 'center',
    width: '7.5rem'
  },
  link: {
    color: theme.palette.primary.main,
    fontWeight: 'bold'
  }
}))

const ToolCard: React.FunctionComponent<ToolCardProps> = (props: ToolCardProps) => {
  const classes = useStyles()

  return (
    <Card className={classes.card}>
      <CardHeader
      action={props.isBeta && <BetaTag />}
        className={classes.cardHeader}
        title={
          <React.Fragment>
            <Link className={classes.link} to={props.route} target="_blank">
              {props.name}
            </Link>
          </React.Fragment>
        }
      />
      <CardContent className={classes.cardContent}>
        <Box className={classes.iconContainer}>{props.icon}</Box>
        <Typography className={classes.cardDescription}>{props.description}</Typography>
      </CardContent>
      <CardActions className={classes.cardActions}>
        <Button
          color="primary"
          href={props.route}
          size="large"
          variant="contained"
          sx={{ fontSize: '1.125rem', fontWeight: 700 }}
          target="_blank"
        >
          Get Started
        </Button>
      </CardActions>
    </Card>
  )
}

export default ToolCard
