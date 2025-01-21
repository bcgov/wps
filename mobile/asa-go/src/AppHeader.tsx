import { Box, Typography } from "@mui/material";
import Grid from "@mui/material/Grid2";

import { theme } from "@/theme";

export const AppHeader = () => {
  return (
    <Box
      sx={{
        height: 100,
        background: theme.palette.primary.main,
        borderBottomWidth: 2,
        borderBottomStyle: "solid",
        borderBottomColor: theme.palette.secondary.main,
      }}
    >
      <Grid
        container
        spacing={1}
        sx={{
          flexGrow: 1,
          width: "fit-content",
          marginTop: 5,
          justifyContent: "space-between",
        }}
      >
        <Grid>
          <Typography
            variant="h2"
            sx={{
              color: theme.palette.primary.contrastText,
              fontSize: "1.7rem",
            }}
          >
            ASA
          </Typography>
        </Grid>
        <Grid>
          <Typography
            variant="h2"
            sx={{
              color: theme.palette.primary.contrastText,
              fontSize: "1.7rem",
            }}
          >
            ASA
          </Typography>
        </Grid>
      </Grid>
    </Box>
  );
};
