import { authenticate } from "@/slices/authenticationSlice";
import { AppDispatch } from "@/store";
import { Button, Typography, useTheme } from "@mui/material";
import { useDispatch } from "react-redux";

interface LoginButonProps {
  label: string;
}

const LoginButton = ({ label }: LoginButonProps) => {
  const dispatch: AppDispatch = useDispatch();
  const theme = useTheme();

  const handleLogin = () => {
    dispatch(authenticate());
  };
  return (
    <Button
      onClick={handleLogin}
      size="large"
      sx={{
        border: "1px solid white",
        color: "white",
        display: "block",
        mt: theme.spacing(5),
      }}
      variant="outlined"
    >
      <Typography
        sx={{
          justifyContent: "center",
          display: "flex",
          fontWeight: "bold",
        }}
      >
        {label}
      </Typography>
    </Button>
  );
};

export default LoginButton;
