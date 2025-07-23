import { render, screen } from "@testing-library/react";
import TabPanel from "./TabPanel";
import { NavPanel } from "@/utils/constants";

describe("TabPanel", () => {
  const panelContent = <div data-testid="panel-content">Panel Content</div>;

  it("renders children when value matches panel", () => {
    render(
      <TabPanel value={NavPanel.MAP} panel={NavPanel.MAP}>
        {panelContent}
      </TabPanel>
    );
    expect(screen.getByTestId("panel-content")).toBeVisible();
  });

  it("does not render children when value does not match panel", () => {
    render(
      <TabPanel value={NavPanel.PROFILE} panel={NavPanel.MAP}>
        {panelContent}
      </TabPanel>
    );
    // tab exists but is hidden
    const content = screen.queryByTestId("panel-content");
    expect(content).not.toBeVisible();
  });

  it("sets hidden prop correctly", () => {
    const { rerender } = render(
      <TabPanel value={NavPanel.MAP} panel={NavPanel.MAP}>
        {panelContent}
      </TabPanel>
    );
    expect(
      screen.getByTestId("panel-content").parentElement
    ).not.toHaveAttribute("hidden");

    rerender(
      <TabPanel value={NavPanel.PROFILE} panel={NavPanel.MAP}>
        {panelContent}
      </TabPanel>
    );
    expect(screen.getByTestId("panel-content").parentElement).toHaveAttribute(
      "hidden"
    );
  });
});
