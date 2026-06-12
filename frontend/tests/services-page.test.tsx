import assert from "node:assert/strict";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { ServicesPage } from "../src/features/services/pages/ServicesPage";

test("renders service management title", () => {
  const html = renderToStaticMarkup(<ServicesPage />);

  assert.match(html, /Current section: Service Catalog/);
  assert.match(html, /Service Catalog/);
  assert.match(html, /Manage monitored services, ownership, and SLA targets\./);
  assert.match(html, /Import from Zabbix/);
});
