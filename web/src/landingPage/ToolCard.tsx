import React from 'react'
import Button from '@mui/material/Button'
import Card from '@mui/material/Card'
import CardActions from '@mui/material/CardActions'
import CardContent from '@mui/material/CardContent'
import CardHeader from '@mui/material/CardHeader'
import Typography from '@mui/material/Typography'

interface ToolCardProps {
  description: string
  icon: React.ReactNode
  name: string
  route: string
}

const ToolCard: React.FunctionComponent<ToolCardProps> = (props: ToolCardProps) => {
  return (
    <Card>
      <CardHeader>{props.name}</CardHeader>
      <CardContent>
        <Typography>{props.description}</Typography>
      </CardContent>
      <CardActions>
        <Button color="primary" href={props.route} variant="contained">
          Get Started
        </Button>
      </CardActions>
    </Card>
  )
}

export default ToolCard
