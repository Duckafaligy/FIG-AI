import { expect, test } from "@playwright/test";

test("projects dashboard renders and filters websites", async ({ page, request }) => {
  const api = await request.get("/api/projects");
  test.skip(!api.ok(), "A signed-in or demo workspace API is required for the dashboard test.");

  await page.goto("/projects");
  await expect(page.getByRole("heading", { name: /Every site\./ })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Projects you can act on." })).toBeVisible();

  const search = page.getByRole("textbox", { name: "Search projects" });
  await search.fill("__no_matching_site__");
  await expect(page.getByText("No matching websites")).toBeVisible();
  await page.getByRole("button", { name: "Clear search" }).click();
  await expect(page.getByText("No matching websites")).toHaveCount(0);
});
