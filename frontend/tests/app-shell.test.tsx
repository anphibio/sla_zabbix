import assert from "node:assert/strict";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import App from "../src/app/App";

test("renders app title", () => {
  const html = renderToStaticMarkup(<App />);

  assert.match(html, /Zabbix SLA/);
  assert.match(html, /Technical dashboard for SLA monitoring/);
  assert.match(html, /Current section: Dashboard/);
  assert.doesNotMatch(html, /Import from Zabbix/);
});
