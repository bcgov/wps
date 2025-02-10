import Grid from "@mui/material/Grid2";
import { Box } from "@mui/material";
import { theme } from "@/theme";
import { Counter } from "@/components/Counter";

export const ASATabs = () => {
  return (
    <Box
      sx={{
        height: 100,
        background: theme.palette.primary.main,
      }}
    >
      <Grid
        container
        spacing={5}
        sx={{
          flexGrow: 1,
          width: "fit-content",
          marginTop: 2,
        }}
      >
        <Grid>
          <Counter />
        </Grid>
      </Grid>
    </Box>
  );
};
