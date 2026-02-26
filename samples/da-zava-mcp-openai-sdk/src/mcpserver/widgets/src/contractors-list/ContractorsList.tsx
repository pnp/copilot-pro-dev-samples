import React, { useState, useCallback } from "react";
import {
  makeStyles,
  Text,
  Badge,
  Card,
  CardHeader,
  Button,
  Divider,
  tokens,
} from "@fluentui/react-components";
import {
  ArrowMaximizeRegular,
  ArrowMinimizeRegular,
  WrenchRegular,
  StarRegular,
  StarFilled,
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
  const contractors = (toolOutput?.contractors ?? []).filter(c => c.isActive);

  const [isFullscreen, setIsFullscreen] = useState(false);
  const toggleFullscreen = useCallback(async () => {
    if (window.openai?.requestDisplayMode) {
      const current = window.openai.displayMode;
      await window.openai.requestDisplayMode({ mode: current === "fullscreen" ? "inline" : "fullscreen" });
      setIsFullscreen(prev => !prev);
      return;
    }
    // Fallback: use native Fullscreen API when host doesn't support requestDisplayMode
    console.warn("requestDisplayMode is not available on this platform — falling back to native fullscreen.");
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
      else await document.exitFullscreen();
    } catch {}
    setIsFullscreen(prev => !prev);
  }, []);

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

      <Text size={300} style={{ color: colors.textSecondary, marginBottom: "12px", display: "block" }}>
        {contractors.length} contractor{contractors.length !== 1 ? "s" : ""}
      </Text>

      <Divider style={{ marginBottom: "12px" }} />

      {/* Contractors Grid */}
      <div className={styles.grid}>
        {contractors.map(contractor => {
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
