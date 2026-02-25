import React, { useState, useCallback, useEffect } from "react";
import {
  Card,
  Text,
  Badge,
  Button,
  Table,
  TableHeader,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  TableCellLayout,
  tokens,
  makeStyles,
  Divider,
  Subtitle1,
  Subtitle2,
  Body1,
  Caption1,
  Title3,
  Avatar,
} from "@fluentui/react-components";
import {
  Mail20Regular,
  Phone20Regular,
  Location20Regular,
  Certificate20Regular,
  Briefcase20Regular,
  ArrowLeft16Regular,
  FullScreenMaximize24Regular,
  FullScreenMinimize24Regular,
} from "@fluentui/react-icons";
import { useOpenAiGlobal } from "../hooks/useOpenAiGlobal";
import type { ConsultantProfileData, Assignment } from "../types";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    padding: "16px",
    fontFamily: '"Segoe Sans", "Segoe UI", "Segoe UI Web (West European)", -apple-system, BlinkMacSystemFont, Roboto, "Helvetica Neue", Arial, sans-serif',
    boxSizing: "border-box",
    width: "100%",
    overflowX: "hidden" as const,
  },
  profileHeader: {
    display: "flex",
    gap: "20px",
    alignItems: "flex-start",
    flexWrap: "wrap" as const,
  },
  photo: {
    width: "80px",
    height: "80px",
    borderRadius: "50%",
    objectFit: "cover" as const,
    border: `3px solid ${tokens.colorBrandBackground}`,
    flexShrink: 0,
  },
  headerInfo: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    flex: 1,
    minWidth: 0,
    overflowWrap: "break-word" as const,
  },
  contactRow: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    color: tokens.colorNeutralForeground2,
    minWidth: 0,
  },
  section: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  sectionHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  tagRow: {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: "6px",
  },
  statsRow: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))",
    gap: "12px",
  },
  statCard: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    padding: "12px 16px",
  },
  tableWrapper: {
    overflowX: "auto" as const,
    width: "100%",
    WebkitOverflowScrolling: "touch" as const,
  },
  noData: {
    padding: "24px",
    textAlign: "center" as const,
    color: tokens.colorNeutralForeground3,
  },
});

export function ConsultantProfile() {
  const styles = useStyles();
  const toolOutput = useOpenAiGlobal<ConsultantProfileData>("toolOutput");
  const data = toolOutput;

  if (!data?.consultant) {
    return (
      <div className={styles.noData}>
        <Body1>No profile loaded. Use the MCP tool to view a consultant profile.</Body1>
      </div>
    );
  }

  const { consultant, assignments = [] } = data;

  // Calculate stats from assignments
  const totalBillableHours = assignments
    .filter((a) => a.billable)
    .reduce((sum, a) => {
      const forecast = a.forecast ?? [];
      return sum + forecast.reduce((s, f) => s + f.hours, 0);
    }, 0);

  const totalDelivered = assignments.reduce((sum, a) => {
    const delivered = a.delivered ?? [];
    return sum + delivered.reduce((s, d) => s + d.hours, 0);
  }, 0);

  const activeProjects = assignments.length;

  // Fullscreen toggle — starts inline, switches on button click
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  const toggleFullscreen = useCallback(async () => {
    if (window.openai?.requestDisplayMode) {
      const current = window.openai.displayMode;
      await window.openai.requestDisplayMode({ mode: current === "fullscreen" ? "inline" : "fullscreen" });
      return;
    }
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
        return;
      } else {
        await document.exitFullscreen();
        return;
      }
    } catch { /* not supported */ }
    setIsFullscreen((prev) => !prev);
  }, []);

  return (
    <div className={styles.root} style={isFullscreen ? {
      position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
      zIndex: 9999, overflowY: "auto", background: tokens.colorNeutralBackground1,
    } : undefined}>
      {/* ── Fullscreen toggle ── */}
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <Button
          appearance="subtle"
          icon={isFullscreen ? <FullScreenMinimize24Regular /> : <FullScreenMaximize24Regular />}
          onClick={toggleFullscreen}
          title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
        />
      </div>

      {/* ── Profile Header ── */}
      <Card>
        <div className={styles.profileHeader}>
          <img
            src={consultant.photoUrl}
            alt={consultant.name}
            className={styles.photo}
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
          <div className={styles.headerInfo}>
            <Title3>{consultant.name}</Title3>

            <div className={styles.contactRow}>
              <Mail20Regular />
              <Body1>{consultant.email}</Body1>
            </div>

            <div className={styles.contactRow}>
              <Phone20Regular />
              <Body1>{consultant.phone}</Body1>
            </div>

            {consultant.location && (
              <div className={styles.contactRow}>
                <Location20Regular />
                <Body1>
                  {consultant.location.city}, {consultant.location.state},{" "}
                  {consultant.location.country}
                </Body1>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* ── Quick Stats ── */}
      <div className={styles.statsRow}>
        <Card className={styles.statCard}>
          <Caption1>Active Projects</Caption1>
          <Title3>{activeProjects}</Title3>
        </Card>
        <Card className={styles.statCard}>
          <Caption1>Forecast Hours</Caption1>
          <Title3>{totalBillableHours}</Title3>
        </Card>
        <Card className={styles.statCard}>
          <Caption1>Delivered Hours</Caption1>
          <Title3>{totalDelivered}</Title3>
        </Card>
      </div>

      <Divider />

      {/* ── Skills ── */}
      {consultant.skills?.length > 0 && (
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <Subtitle2>Skills</Subtitle2>
          </div>
          <div className={styles.tagRow}>
            {consultant.skills.map((skill) => (
              <Badge key={skill} appearance="outline" size="medium" color="informative">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* ── Certifications ── */}
      {consultant.certifications?.length > 0 && (
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <Certificate20Regular />
            <Subtitle2>Certifications</Subtitle2>
          </div>
          <div className={styles.tagRow}>
            {consultant.certifications.map((cert) => (
              <Badge key={cert} appearance="filled" size="medium" color="success">
                {cert}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* ── Roles ── */}
      {consultant.roles?.length > 0 && (
        <div className={styles.section}>
          <div className={styles.sectionHeader}>
            <Briefcase20Regular />
            <Subtitle2>Roles</Subtitle2>
          </div>
          <div className={styles.tagRow}>
            {consultant.roles.map((role) => (
              <Badge key={role} appearance="filled" size="medium" color="brand">
                {role}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <Divider />

      {/* ── Assignments ── */}
      <div className={styles.section}>
        <Subtitle1>Assignments</Subtitle1>
        {assignments.length > 0 ? (
          <div className={styles.tableWrapper}>
          <Table size="small" style={{ minWidth: "520px" }}>
            <TableHeader>
              <TableRow>
                <TableHeaderCell>Project</TableHeaderCell>
                <TableHeaderCell>Role</TableHeaderCell>
                <TableHeaderCell>Billable</TableHeaderCell>
                <TableHeaderCell>Rate</TableHeaderCell>
                <TableHeaderCell>Forecast Hrs</TableHeaderCell>
                <TableHeaderCell>Delivered Hrs</TableHeaderCell>
              </TableRow>
            </TableHeader>
            <TableBody>
              {assignments.map((asn, idx) => {
                const forecastHrs = (asn.forecast ?? []).reduce(
                  (s, f) => s + f.hours,
                  0
                );
                const deliveredHrs = (asn.delivered ?? []).reduce(
                  (s, d) => s + d.hours,
                  0
                );
                return (
                  <TableRow key={idx}>
                    <TableCell>
                      <TableCellLayout>
                        <Body1>{asn.projectName ?? `Project ${asn.projectId}`}</Body1>
                      </TableCellLayout>
                    </TableCell>
                    <TableCell>
                      <Badge appearance="outline" size="small">
                        {asn.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        appearance="filled"
                        size="small"
                        color={asn.billable ? "success" : "warning"}
                      >
                        {asn.billable ? "Yes" : "No"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Body1>${asn.rate}/hr</Body1>
                    </TableCell>
                    <TableCell>
                      <Body1>{forecastHrs}</Body1>
                    </TableCell>
                    <TableCell>
                      <Body1>{deliveredHrs}</Body1>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
          </div>
        ) : (
          <Caption1>No assignments found for this consultant.</Caption1>
        )}
      </div>
    </div>
  );
}
