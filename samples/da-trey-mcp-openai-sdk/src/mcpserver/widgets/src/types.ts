/**
 * Shared types for widget structured content from MCP tools.
 */

export interface Location {
  street: string;
  city: string;
  state: string;
  country: string;
  postalCode: string;
  latitude: number;
  longitude: number;
}

export interface Consultant {
  id: string;
  name: string;
  email: string;
  phone: string;
  photoUrl: string;
  location: Location;
  skills: string[];
  certifications: string[];
  roles: string[];
}

export interface Project {
  id: string;
  name: string;
  description: string;
  clientName: string;
  clientContact: string;
  clientEmail: string;
  location: Location;
}

export interface ForecastEntry {
  month: number;
  year: number;
  hours: number;
}

export interface Assignment {
  id: string;
  projectId: string;
  consultantId: string;
  role: string;
  billable: boolean;
  rate: number;
  forecast: ForecastEntry[];
  delivered: ForecastEntry[];
  projectName?: string;
  clientName?: string;
  consultantName?: string;
}

export interface DashboardSummary {
  totalConsultants: number;
  totalProjects: number;
  totalAssignments: number;
  totalBillableHours: number;
  searchApplied?: boolean;
  searchCriteria?: { skill?: string; name?: string };
}

export interface DashboardFilters {
  consultantName?: string;
  projectName?: string;
  projectIds?: string[];
  skill?: string;
  role?: string;
  billable?: boolean;
}

export interface DashboardData {
  consultants: Consultant[];
  projects: Project[];
  assignments?: Assignment[];
  summary: DashboardSummary;
  filters?: DashboardFilters;
}

export interface ConsultantProfileData {
  consultant: Consultant;
  assignments: Assignment[];
}

export interface BulkEditorData {
  consultants: Consultant[];
}

export type Theme = "light" | "dark";
export type DisplayMode = "inline" | "expanded";
