import { styled, Typography } from "@mui/material";

const StyledDescription = styled(Typography)(({ theme }) => ({
  [theme.breakpoints.down("sm")]: { maxWidth: "80%" },
  [theme.breakpoints.up("sm")]: { maxWidth: "50%" },
}));

const AppDescription = () => {
  return (
    <StyledDescription
      data-testid="app-description"
      sx={{
        color: "white",
        display: "flex",
        textAlign: "center",
        fontWeight: "bold",
      }}
      variant="body1"
    >
      {
        "A spatial analysis tool that automates the continuous monitoring, updating, and communication of anticipated fire behaviour that will challenge direct suppression efforts and put the safety of responders at risk."
      }
    </StyledDescription>
  );
};

export default AppDescription;
