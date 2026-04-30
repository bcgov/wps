import SideNavigationListItem from "@/components/SideNavigationListItem";
import { theme } from "@/theme";
import { NavPanel } from "@/utils/constants";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import MapIcon from "@mui/icons-material/Map";
import SettingsIcon from "@mui/icons-material/Settings";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import { Drawer, List, styled } from "@mui/material";

const StyledDrawer = styled(Drawer)({
  width: "calc(100px + env(safe-area-inset-left))",
  flexShrink: 0,
  "& .MuiDrawer-paper": {
    width: "calc(100px + env(safe-area-inset-left))",
    boxSizing: "border-box",
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    paddingLeft: "env(safe-area-inset-left)",
  },
});

interface SideNavigationProps {
  tab: NavPanel;
  setTab: (newValue: NavPanel) => void;
}

const SideNavigation = ({ tab, setTab }: SideNavigationProps) => {
  return (
    <StyledDrawer variant="permanent" anchor="left">
      <List
        sx={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <SideNavigationListItem
          icon={<MapIcon sx={{ fontSize: "40px" }} />}
          navItem={NavPanel.MAP}
          setTab={setTab}
          tab={tab}
        />
        <SideNavigationListItem
          icon={<TextSnippetIcon sx={{ fontSize: "40px" }} />}
          navItem={NavPanel.PROFILE}
          setTab={setTab}
          tab={tab}
        />
        <SideNavigationListItem
          icon={<AnalyticsIcon sx={{ fontSize: "40px" }} />}
          navItem={NavPanel.ADVISORY}
          setTab={setTab}
          tab={tab}
        />
        <SideNavigationListItem
          icon={<SettingsIcon sx={{ fontSize: "40px" }} />}
          navItem={NavPanel.SETTINGS}
          setTab={setTab}
          tab={tab}
        />
      </List>
    </StyledDrawer>
  );
};

export default SideNavigation;
