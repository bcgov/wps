import React from 'react'
import Button from '@mui/material/Button'
import Card from '@mui/material/Card'
import CardActions from '@mui/material/CardActions'
import CardContent from '@mui/material/CardContent'
import CardHeader from '@mui/material/CardHeader'
import Typography from '@mui/material/Typography'
import makeStyles from '@mui/styles/makeStyles'
import { theme } from 'app/theme'

interface ToolCardProps {
  description: React.ReactNode | string
  icon: React.ReactNode
  name: string
  route: string
}

const useStyles = makeStyles(() => ({
  button: {
    height: '3rem',
    width: '11.5rem'
  },
  card: {
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    maxWidth: '400px',
    paddingBottom: '1rem'
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
    paddingLeft: '2rem',
    paddingRight: '2rem',
    paddingTop: '0px'
  },
  cardDescription: {
    paddingTop: '1rem'
  },
  cardHeader: {
    color: theme.palette.primary.main,
    textAlign: 'center'
  },
  iconContainer: {
    alignItems: 'center',
    borderColor: '#D9D9D9',
    borderRadius: '50%',
    borderStyle: 'solid',
    borderWidth: '1px',
    display: 'flex',
    height: '8.5rem',
    justifyContent: 'center',
    paddingBottom: '1rem',
    width: '8.5rem'
  }
}))

const ToolCard: React.FunctionComponent<ToolCardProps> = (props: ToolCardProps) => {
    const classes = useStyles()

  return (
    <Card className={classes.card}>
      <CardHeader className={classes.cardHeader}title={props.name}></CardHeader>
      <CardContent className={classes.cardContent}>
        <div className={classes.iconContainer}>
          {props.icon}
        </div>
        <Typography className={classes.cardDescription}>{props.description}</Typography>
      </CardContent>
      <CardActions className={classes.cardActions}>
        <Button color="primary" href={props.route} size='large' variant="contained" sx={{fontSize: '1.125rem', fontWeight: 700}}>
          Get Started
          
        </Button>
      </CardActions>
    </Card>
  )
}

export default ToolCard
