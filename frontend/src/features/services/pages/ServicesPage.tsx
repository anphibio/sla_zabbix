import React from "react";

import { AppLayout } from "../../../components/AppLayout";
import { PageHeader } from "../../../components/PageHeader";

const panelStyle = {
  padding: "20px",
  border: "1px solid #334155",
  borderRadius: "16px",
  backgroundColor: "#111c34",
};

const listStyle = {
  margin: "16px 0 0",
  paddingLeft: "18px",
  color: "#cbd5e1",
};

export function ServicesPage() {
  return (
    <AppLayout currentSection="Service Catalog">
      <section style={{ display: "grid", gap: "16px" }}>
        <PageHeader
          eyebrow="SERVICES"
          title="Service Catalog"
          description="Manage monitored services, ownership, and SLA targets."
        />
        <div style={panelStyle}>
          <p style={{ margin: 0, color: "#cbd5e1" }}>
            Connect technical services from Zabbix to internal ownership and target rules so the
            SLA engine can calculate availability with clear accountability.
          </p>
          <ul style={listStyle}>
            <li>Import from Zabbix</li>
            <li>Review ownership metadata</li>
            <li>Track SLA target configuration</li>
          </ul>
        </div>
      </section>
    </AppLayout>
  );
}
