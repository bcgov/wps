import { NavPanel } from "@/utils/constants";
import { Box } from "@mui/material";

interface TabPanelProps {
  value: NavPanel;
  panel: NavPanel;
  children: React.ReactNode;
}

const TabPanel = ({ value, panel, children }: TabPanelProps) => (
  <Box
    hidden={value !== panel}
    sx={{
      flexGrow: 1,
      flexDirection: "column",
      overflow: "hidden",
      display: value === panel ? "flex" : "none",
      width: "100%",
      height: "100%",
    }}
  >
    {children}
  </Box>
);

export default TabPanel;
