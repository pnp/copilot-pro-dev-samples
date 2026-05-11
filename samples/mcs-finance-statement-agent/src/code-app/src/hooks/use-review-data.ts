import { useQuery } from "@tanstack/react-query";
import { fetchJobByJobId, fetchStatementsByJobId, fetchLineItemsByJobId } from "@/services/dataverse-service";

export function useReviewData(jobId: string | null) {
  const jobQuery = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => fetchJobByJobId(jobId!),
    enabled: !!jobId,
  });

  const statementsQuery = useQuery({
    queryKey: ["statements", jobId],
    queryFn: () => fetchStatementsByJobId(jobId!),
    enabled: !!jobId,
  });

  const lineItemsQuery = useQuery({
    queryKey: ["lineItems", jobId],
    queryFn: () => fetchLineItemsByJobId(jobId!),
    enabled: !!jobId,
  });

  return {
    job: jobQuery.data ?? null,
    statements: statementsQuery.data ?? [],
    lineItems: lineItemsQuery.data ?? [],
    isLoading: jobQuery.isLoading || statementsQuery.isLoading || lineItemsQuery.isLoading,
    error: jobQuery.error || statementsQuery.error || lineItemsQuery.error,
  };
}
