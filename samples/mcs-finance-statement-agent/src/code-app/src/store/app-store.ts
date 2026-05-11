import { create } from "zustand";
import type { ReviewLineItem } from "@/types/extraction";

interface AppState {
  jobId: string | null;
  setJobId: (jobId: string | null) => void;

  lineItems: ReviewLineItem[];
  setLineItems: (items: ReviewLineItem[]) => void;
  updateLineItem: (recordId: string, updates: Partial<ReviewLineItem>) => void;

  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  jobId: null,
  setJobId: (jobId) => set({ jobId }),

  lineItems: [],
  setLineItems: (items) => set({ lineItems: items }),
  updateLineItem: (recordId, updates) =>
    set((s) => ({
      lineItems: s.lineItems.map((item) =>
        item.recordId === recordId ? { ...item, ...updates } : item
      ),
    })),

  activeTab: "BalanceSheet",
  setActiveTab: (tab) => set({ activeTab: tab }),
}));
