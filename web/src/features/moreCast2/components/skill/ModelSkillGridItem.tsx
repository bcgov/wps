import { ModelSkillEnum, RankedModelSkillStats } from '@/api/skillAPI'
import { Button, Grid } from '@mui/material'

interface ModelSkillGridItemProps {
  addSelectedModel: (selectedModel: ModelSkillEnum) => void
  stats: RankedModelSkillStats
}

const ModelSkillGridItem = ({ addSelectedModel, stats }: ModelSkillGridItemProps) => {
  return (
    <Grid container>
      <Grid item xs={3}>
        {stats.model}
      </Grid>
      <Grid item xs={3}>
        {stats.rmse.toFixed(1)}
      </Grid>
      <Grid item xs={3}>
        {stats.rank}
      </Grid>
      <Grid item xs={3}>
        <Button size="small" variant="outlined" onClick={() => addSelectedModel(stats.model)}>
          Select
        </Button>
      </Grid>
    </Grid>
  )
}

export default ModelSkillGridItem
