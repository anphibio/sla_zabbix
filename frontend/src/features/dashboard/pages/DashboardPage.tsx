import React from "react";

import { AppLayout } from "../../../components/AppLayout";
import { PageHeader } from "../../../components/PageHeader";
import { StatCard } from "../../../components/StatCard";

const statsGridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
  gap: "16px",
};

export function DashboardPage() {
  return (
    <AppLayout currentSection="Dashboard">
      <section style={{ display: "grid", gap: "16px" }}>
        <PageHeader
          eyebrow="OVERVIEW"
          title="Technical dashboard for SLA monitoring"
          description="Monitor service coverage, visibility from Zabbix, and the initial operational baseline for SLA calculations."
        />
        <div style={statsGridStyle}>
          <StatCard
            label="Tracked services"
            value="Placeholder"
            hint="Baseline card for future catalog totals"
          />
          <StatCard
            label="Zabbix sync"
            value="Pending"
            hint="Preparatory state until live integration data is wired in"
          />
          <StatCard
            label="SLA target baseline"
            value="To be defined"
            hint="Placeholder for default targets after rule configuration"
          />
        </div>
      </section>
    </AppLayout>
  );
}
