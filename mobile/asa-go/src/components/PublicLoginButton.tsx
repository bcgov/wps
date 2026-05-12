import { Button } from "@mui/material";

const PublicLoginButton = () => {
  return (
    <Button
      onClick={() => console.log("PublicLoginButton clicked")}
      sx={{ color: "white", textDecoration: "underline" }}
    >
      Continue as guest
    </Button>
  );
};

export default PublicLoginButton;
