import { test, expect } from "@playwright/test";

test("health endpoint", async ({ request }) => {
  const res = await request.get("/health");
  expect(res.ok()).toBeTruthy();
});
