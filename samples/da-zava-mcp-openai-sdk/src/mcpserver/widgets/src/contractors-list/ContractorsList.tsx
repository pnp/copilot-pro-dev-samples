import React, { useState, useCallback, useMemo } from "react";
import {
  makeStyles,
  Text,
  Badge,
  Card,
  CardHeader,
  Input,
  Button,
  Divider,
  Switch,
  tokens,
} from "@fluentui/react-components";
import {
  SearchRegular,
  ArrowMaximizeRegular,
  ArrowMinimizeRegular,
  WrenchRegular,
  StarRegular,
  StarFilled,
  PersonRegular,
  MailRegular,
  PhoneRegular,
  LocationRegular,
  CertificateFilled,
} from "@fluentui/react-icons";
import { useOpenAiGlobal } from "../hooks/useOpenAiGlobal";
import { useThemeColors } from "../hooks/useThemeColors";
import type { ContractorsListData, Contractor } from "../types";

const useStyles = makeStyles({
  container: { padding: "16px", fontFamily: tokens.fontFamilyBase },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" },
  filters: { display: "flex", gap: "8px", marginBottom: "16px", flexWrap: "wrap" as const, alignItems: "center" },
  grid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "12px" },
  card: { padding: "12px", borderRadius: "8px" },
  infoRow: { display: "flex", alignItems: "center", gap: "6px", marginTop: "4px" },
  tags: { display: "flex", gap: "4px", flexWrap: "wrap" as const, marginTop: "8px" },
  rating: { display: "flex", alignItems: "center", gap: "2px" },
});

function renderStars(rating: number) {
  const stars = [];
  for (let i = 1; i <= 5; i++) {
    stars.push(
      i <= Math.round(rating)
        ? <StarFilled key={i} style={{ color: "#ffb900", fontSize: "14px" }} />
        : <StarRegular key={i} style={{ color: "#ccc", fontSize: "14px" }} />
    );
  }
  return stars;
}

export function ContractorsList() {
  const styles = useStyles();
  const colors = useThemeColors();
  const toolOutput = useOpenAiGlobal("toolOutput") as ContractorsListData | null;
  const contractors = toolOutput?.contractors ?? [];

  const [search, setSearch] = useState("");
  const [preferredOnly, setPreferredOnly] = useState(false);

  const [isFullscreen, setIsFullscreen] = useState(false);
  const toggleFullscreen = useCallback(async () => {
    if (window.openai?.requestDisplayMode) {
      const current = window.openai.displayMode;
      await window.openai.requestDisplayMode({ mode: current === "fullscreen" ? "inline" : "fullscreen" });
      return;
    }
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
      else await document.exitFullscreen();
    } catch {}
    setIsFullscreen(prev => !prev);
  }, []);

  const filtered = useMemo(() => {
    return contractors.filter(c => {
      const matchesSearch = !search ||
        c.name.toLowerCase().includes(search.toLowerCase()) ||
        c.businessName.toLowerCase().includes(search.toLowerCase()) ||
        c.specialties.some(s => s.toLowerCase().includes(search.toLowerCase()));
      const matchesPreferred = !preferredOnly || c.isPreferred;
      return matchesSearch && matchesPreferred && c.isActive;
    });
  }, [contractors, search, preferredOnly]);

  return (
    <div className={styles.container} style={{ backgroundColor: colors.background, color: colors.text }}>
      {/* Header */}
      <div className={styles.header}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <WrenchRegular style={{ fontSize: "24px", color: colors.primary }} />
          <Text size={600} weight="bold">Zava Insurance — Contractors</Text>
        </div>
        <Button
          icon={isFullscreen ? <ArrowMinimizeRegular /> : <ArrowMaximizeRegular />}
          appearance="subtle"
          onClick={toggleFullscreen}
        />
      </div>

      {/* Filters */}
      <div className={styles.filters}>
        <Input
          placeholder="Search contractors or specialties..."
          contentBefore={<SearchRegular />}
          value={search}
          onChange={(_, d) => setSearch(d.value)}
          style={{ flex: "1 1 250px" }}
        />
        <Switch
          label="Preferred only"
          checked={preferredOnly}
          onChange={(_, d) => setPreferredOnly(d.checked)}
        />
      </div>

      <Text size={300} style={{ color: colors.textSecondary, marginBottom: "12px", display: "block" }}>
        Showing {filtered.length} of {contractors.length} contractors
      </Text>

      <Divider style={{ marginBottom: "12px" }} />

      {/* Contractors Grid */}
      <div className={styles.grid}>
        {filtered.map(contractor => {
          const addr = typeof contractor.address === "object" && contractor.address
            ? contractor.address
            : null;

          return (
            <Card key={contractor.id} className={styles.card} style={{ backgroundColor: colors.surface }}>
              <CardHeader
                header={
                  <div style={{ display: "flex", justifyContent: "space-between", width: "100%", alignItems: "center" }}>
                    <div>
                      <Text weight="semibold">{contractor.name}</Text>
                      {contractor.isPreferred && (
                        <Badge appearance="tint" size="small" color="success" style={{ marginLeft: "6px" }}>
                          Preferred
                        </Badge>
                      )}
                    </div>
                    <div className={styles.rating}>
                      {renderStars(contractor.rating)}
                      <Text size={200} style={{ marginLeft: "4px" }}>{contractor.rating}</Text>
                    </div>
                  </div>
                }
                description={
                  <Text size={200} style={{ color: colors.textSecondary }}>{contractor.businessName}</Text>
                }
              />
              <div className={styles.infoRow}>
                <MailRegular style={{ fontSize: "14px", color: colors.textSecondary }} />
                <Text size={200}>{contractor.email}</Text>
              </div>
              <div className={styles.infoRow}>
                <PhoneRegular style={{ fontSize: "14px", color: colors.textSecondary }} />
                <Text size={200}>{contractor.phone}</Text>
              </div>
              {addr && (
                <div className={styles.infoRow}>
                  <LocationRegular style={{ fontSize: "14px", color: colors.textSecondary }} />
                  <Text size={200}>{addr.city}, {addr.state} {addr.zipCode}</Text>
                </div>
              )}
              <div className={styles.infoRow}>
                <CertificateFilled style={{ fontSize: "14px", color: colors.textSecondary }} />
                <Text size={200}>License: {contractor.licenseNumber}</Text>
              </div>
              <div className={styles.tags}>
                {contractor.specialties.map((s, i) => (
                  <Badge key={i} appearance="outline" size="small">{s}</Badge>
                ))}
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
