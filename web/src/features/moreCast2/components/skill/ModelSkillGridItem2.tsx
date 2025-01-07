import { ModelSkillEnum, RankedModelSkillSummaryData } from '@/api/skillAPI'
import { Button, Grid } from '@mui/material'

interface ModelSkillGridItemProps {
  addSelectedModel: (selectedModel: ModelSkillEnum) => void
  stats: RankedModelSkillSummaryData
}

const ModelSkillGridItem2 = ({ addSelectedModel, stats }: ModelSkillGridItemProps) => {
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
        <Button size="small" variant="contained" onClick={() => addSelectedModel(stats.model as ModelSkillEnum)}>
          Select
        </Button>
      </Grid>
    </Grid>
  )
}

export default ModelSkillGridItem2
