import { Button } from "@mui/material";

const PublicLoginButton = () => {
  return (
    <Button
      onClick={() => console.log("PublicLoginButton clicked")}
      sx={{ color: "white", textDecoration: "underline" }}
    >
      Log-in as Guest
    </Button>
  );
};

export default PublicLoginButton;
