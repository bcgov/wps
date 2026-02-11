import { theme } from "@/theme";
import { Drawer, List, styled } from "@mui/material";
import MapIcon from "@mui/icons-material/Map";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import TextSnippetIcon from "@mui/icons-material/TextSnippet";
import { NavPanel } from "@/utils/constants";
import SideNavigationListItem from "@/components/SideNavigationListItem";

const StyledDrawer = styled(Drawer)({
  width: 100,
  flexShrink: 0,
  "& .MuiDrawer-paper": {
    width: 100,
    boxSizing: "border-box",
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
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
          icon={<AnalyticsIcon sx={{ fontSize: "40px" }} />}
          navItem={NavPanel.ADVISORY}
          setTab={setTab}
          tab={tab}
        />
        <SideNavigationListItem
          icon={<TextSnippetIcon sx={{ fontSize: "40px" }} />}
          navItem={NavPanel.PROFILE}
          setTab={setTab}
          tab={tab}
        />
      </List>
    </StyledDrawer>
  );
};

export default SideNavigation;
