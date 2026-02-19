// ── Shared type definitions for Zava Insurance widgets ─────────────────

export interface Claim {
  id: string;
  claimNumber: string;
  policyNumber: string;
  policyHolderName: string;
  policyHolderEmail: string;
  property: string;
  dateOfLoss: string;
  dateReported: string;
  status: string;
  damageTypes: string[];
  description: string;
  estimatedLoss: number;
  adjusterAssigned: string;
  notes: string[];
  createdAt: string;
  updatedAt: string;
}

export interface Contractor {
  id: string;
  name: string;
  businessName: string;
  email: string;
  phone: string;
  address: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };
  licenseNumber: string;
  insuranceCertificate: string;
  specialties: string[];
  rating: number;
  isPreferred: boolean;
  isActive: boolean;
}

export interface Inspection {
  id: string;
  claimId: string;
  claimNumber: string;
  taskType: string;
  priority: string;
  status: string;
  scheduledDate: string;
  inspectorId: string;
  property: string;
  instructions: string;
  photos: string[];
  findings: string;
  recommendedActions: string[];
  flaggedIssues: string[];
  createdAt: string;
  updatedAt: string;
  completedDate: string;
}

export interface Inspector {
  id: string;
  name: string;
  email: string;
  phone: string;
  licenseNumber: string;
  specializations: string[];
}

export interface LineItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  totalPrice: number;
  category: string;
}

export interface PurchaseOrder {
  id: string;
  poNumber: string;
  claimId: string;
  claimNumber: string;
  contractorId: string;
  workDescription: string;
  lineItems: LineItem[];
  subtotal: number;
  tax: number;
  total: number;
  status: string;
  createdDate: string;
  notes: string[];
}

// ── Widget data payloads ───────────────────────────────────────────────
export interface ClaimsDashboardData {
  claims: Claim[];
  inspections: Inspection[];
  purchaseOrders: PurchaseOrder[];
  contractors: Record<string, Contractor>;
  inspectors: Record<string, Inspector>;
}

export interface ClaimDetailData {
  claim: Claim;
  inspections: Inspection[];
  purchaseOrders: PurchaseOrder[];
  contractors: Record<string, Contractor>;
  inspectors: Record<string, Inspector>;
}

export interface ContractorsListData {
  contractors: Contractor[];
}
