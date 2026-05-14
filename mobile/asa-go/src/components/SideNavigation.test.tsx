import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import SideNavigation from "@/components/SideNavigation";
import { NavPanel } from "@/utils/constants";

// Mock SideNavigationListItem to inspect props
vi.mock("@/components/SideNavigationListItem", () => ({
  default: ({
    navItem,
    tab,
  }: {
    icon: React.ReactNode;
    navItem: NavPanel;
    tab: NavPanel;
    setTab: (newValue: NavPanel) => void;
  }) => (
    <div
      data-testid={`nav-item-${navItem.toLowerCase()}`}
      data-navitem={navItem}
      data-tab={tab}
    >
      {navItem}
    </div>
  ),
}));

describe("SideNavigation", () => {
  const mockSetTab = vi.fn();

  it("renders all navigation items", () => {
    render(<SideNavigation tab={NavPanel.MAP} setTab={mockSetTab} />);

    // Check if all nav items are rendered
    expect(screen.getByTestId("nav-item-map")).toBeInTheDocument();
    expect(screen.getByTestId("nav-item-advisory")).toBeInTheDocument();
    expect(screen.getByTestId("nav-item-profile")).toBeInTheDocument();
  });

  it("renders each nav item with correct props", () => {
    render(<SideNavigation tab={NavPanel.MAP} setTab={mockSetTab} />);

    // Check nav items have correct navItem and tab props
    const mapItem = screen.getByTestId("nav-item-map");
    expect(mapItem).toHaveAttribute("data-navitem", NavPanel.MAP);
    expect(mapItem).toHaveAttribute("data-tab", NavPanel.MAP);

    const advisoryItem = screen.getByTestId("nav-item-advisory");
    expect(advisoryItem).toHaveAttribute("data-navitem", NavPanel.ADVISORY);
    expect(advisoryItem).toHaveAttribute("data-tab", NavPanel.MAP);

    const profileItem = screen.getByTestId("nav-item-profile");
    expect(profileItem).toHaveAttribute("data-navitem", NavPanel.PROFILE);
    expect(profileItem).toHaveAttribute("data-tab", NavPanel.MAP);
  });

  it("passes selected tab information to SideNavigationListItem", () => {
    render(<SideNavigation tab={NavPanel.ADVISORY} setTab={mockSetTab} />);

    // Verify tab prop is passed correctly
    expect(screen.getByTestId("nav-item-map")).toHaveAttribute(
      "data-tab",
      NavPanel.ADVISORY,
    );
    expect(screen.getByTestId("nav-item-advisory")).toHaveAttribute(
      "data-tab",
      NavPanel.ADVISORY,
    );
    expect(screen.getByTestId("nav-item-profile")).toHaveAttribute(
      "data-tab",
      NavPanel.ADVISORY,
    );
  });

  it("renders correctly with different selected tabs", () => {
    const navItems = Object.values(NavPanel);

    navItems.forEach((selectedTab) => {
      const { unmount } = render(
        <SideNavigation tab={selectedTab} setTab={mockSetTab} />,
      );

      // Check if all items receive the selected tab
      navItems.forEach((navItem) => {
        const item = screen.getByTestId(`nav-item-${navItem.toLowerCase()}`);
        expect(item).toHaveAttribute("data-tab", selectedTab);
      });

      unmount();
    });
  });
});
