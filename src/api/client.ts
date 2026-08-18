import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type {
  AIConfig,
  CodebookVariable,
  MappingRecord,
  Study,
} from "@/types";

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

// ── Low-level fetch helpers ──────────────────────────────────────────────────

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) {
    const msg = await r.text().catch(() => r.statusText);
    throw new Error(msg);
  }
  return r.json() as Promise<T>;
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: body !== undefined ? { "Content-Type": "application/json" } : {},
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) {
    const msg = await r.text().catch(() => r.statusText);
    throw new Error(msg);
  }
  return r.json() as Promise<T>;
}

async function put<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "PUT",
    headers: body !== undefined ? { "Content-Type": "application/json" } : {},
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) {
    const msg = await r.text().catch(() => r.statusText);
    throw new Error(msg);
  }
  return r.json() as Promise<T>;
}

async function del<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`, { method: "DELETE" });
  if (!r.ok) {
    const msg = await r.text().catch(() => r.statusText);
    throw new Error(msg);
  }
  return r.json() as Promise<T>;
}

// ── Response types ───────────────────────────────────────────────────────────

export interface CodebookUploadResponse {
  status: string;
  row_count: number;
  columns: string[];
  warnings: string[];
}

export interface StudyUploadResponse {
  study_name: string;
  variable_count: number;
  has_example_data: boolean;
  has_context_pdf: boolean;
  warnings: string[];
}

export interface ProviderInfo {
  id: string;
  name: string;
  requires_api_key: boolean;
  requires_base_url: boolean;
  default_base_url?: string;
  supports_embeddings: boolean;
  default_chat_model?: string;
  default_embedding_model?: string;
  api_key_pattern?: string;
  requires_deployment?: boolean;
  note?: string;
}

export interface SlotTestResult {
  connected: boolean;
  message: string;
}

export interface AITestResponse {
  connected: boolean;
  chat: SlotTestResult;
  embedding?: SlotTestResult | null;
}

export interface StudyInitStatus {
  name: string;
  descriptions_generated: boolean;
  embeddings_ready: boolean;
  recommendations_ready: boolean;
  pid_date_ready: boolean;
}

export interface InitialiseStatusResponse {
  codebook_embedded: boolean;
  studies: StudyInitStatus[];
}

export interface RecommendationItem {
  codebook_var: string;
  description: string;
  confidence: number;
}

export interface PIDRecommendationItem {
  variable_name: string;
  confidence: number;
}

export interface VariableDetailResponse {
  variable: {
    variable_name: string;
    description?: string;
    target_recommendations?: string[];
    target_distances?: number[];
    PID_recommendations?: string[];
    PID_distances?: number[];
    date_recommendations?: string[];
    date_distances?: number[];
  };
  example_data: string[];
  recommendations: RecommendationItem[];
  pid_recommendations: PIDRecommendationItem[];
  date_recommendations: PIDRecommendationItem[];
  existing_mapping: MappingRecord & { best_confidence?: number };
  already_used_codebook_vars: string[];
}

export interface MappingsListResponse {
  study: string;
  total: number;
  mapped: number;
  progress: number;
  records: (MappingRecord & { best_confidence?: number })[];
}

export interface TransformationPreviewItem {
  original: string;
  transformed: string;
}

export interface TransformationPreviewResponse {
  preview: TransformationPreviewItem[];
  transformed_count: number;
  blank_count: number;
  valid: boolean;
  error?: string;
}

export interface ValidateExpressionResponse {
  valid: boolean;
  message: string;
}

export interface MappingUpdateRequest {
  codebook_var?: string;
  marked: MappingRecord["marked"];
  notes?: string;
  transformation_type?: "Direct" | "Categorical";
  transformation_instructions?: string;
  source_dtype?: string;
  target_dtype?: string;
  patient_id_var?: string;
  date_var?: string;
  operator_name?: string;
}

// ── API functions ────────────────────────────────────────────────────────────

export const api = {
  // Codebook
  getCodebookMeta: (): Promise<{
    exists: boolean;
    filename?: string;
    row_count?: number;
    uploaded_at?: string;
  }> => get("/api/codebook/meta"),

  uploadCodebook: async (file: File): Promise<CodebookUploadResponse> => {
    const fd = new FormData();
    fd.append("file", file);
    const r = await fetch(`${BASE}/api/codebook/upload`, { method: "POST", body: fd });
    if (!r.ok) throw new Error(await r.text().catch(() => r.statusText));
    return r.json();
  },
  getCodebook: (): Promise<CodebookVariable[]> =>
    get("/api/codebook/"),

  // Studies
  uploadStudy: async (
    name: string,
    variables: File,
    exampleData?: File,
    contextPdf?: File
  ): Promise<StudyUploadResponse> => {
    const fd = new FormData();
    fd.append("study_title", name);
    fd.append("variables_file", variables);
    if (exampleData) fd.append("example_data_file", exampleData);
    if (contextPdf) fd.append("context_pdf", contextPdf);
    const r = await fetch(`${BASE}/api/studies/upload`, { method: "POST", body: fd });
    if (!r.ok) throw new Error(await r.text().catch(() => r.statusText));
    return r.json();
  },
  getStudies: (): Promise<Study[]> => get("/api/studies/"),
  deleteStudy: (name: string): Promise<unknown> => del(`/api/studies/${name}`),

  // AI Config
  getProviders: (): Promise<ProviderInfo[]> => get("/api/ai-config/providers"),
  testConnection: (config: AIConfig): Promise<AITestResponse> =>
    post("/api/ai-config/test", config),
  getProviderModels: (provider: string, baseUrl?: string, apiKey?: string): Promise<{ models: string[] }> => {
    const params = new URLSearchParams({ provider });
    if (baseUrl) params.set("base_url", baseUrl);
    if (apiKey) params.set("api_key", apiKey);
    return get(`/api/ai-config/models?${params.toString()}`);
  },

  // Initialise
  getInitialiseStatus: (): Promise<InitialiseStatusResponse> =>
    get("/api/initialise/status"),
  clearWorkspace: (): Promise<unknown> =>
    post("/api/initialise/clear-workspace"),

  // Mappings
  getMappings: (study: string, status?: string): Promise<MappingsListResponse> => {
    const qs = status ? `?status=${encodeURIComponent(status)}` : "";
    return get(`/api/mappings/${study}${qs}`);
  },
  getVariableDetail: (study: string, variable: string): Promise<VariableDetailResponse> =>
    get(`/api/mappings/${study}/variable/${encodeURIComponent(variable)}`),
  saveMapping: (study: string, variable: string, body: MappingUpdateRequest): Promise<MappingRecord> =>
    put(`/api/mappings/${study}/variable/${encodeURIComponent(variable)}`, body),
  reopenMapping: (study: string, variable: string): Promise<unknown> =>
    put(`/api/mappings/${study}/variable/${encodeURIComponent(variable)}/reopen`),
  getAudit: (study: string, n?: number): Promise<{ records: unknown[] }> => {
    const qs = n !== undefined ? `?n=${n}` : "";
    return get(`/api/mappings/${study}/audit${qs}`);
  },

  // Transformation
  previewTransformation: (body: {
    example_data: string[];
    transformation_type: "Direct" | "Categorical";
    transformation_instructions: string;
    source_dtype?: string;
    target_dtype?: string;
  }): Promise<TransformationPreviewResponse> =>
    post("/api/mappings/preview-transformation", body),
  validateExpression: (expression: string): Promise<ValidateExpressionResponse> =>
    post("/api/mappings/validate-expression", { expression }),

  // Download
  getMappingCsvUrl: (study: string): string =>
    `${BASE}/api/download/${study}/mapping-csv`,
  getAuditLogUrl: (): string => `${BASE}/api/download/audit-log`,
  downloadTransformedData: async (studies: string[]): Promise<Blob> => {
    const r = await fetch(`${BASE}/api/download/transformed-data`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ studies }),
    });
    if (!r.ok) throw new Error(await r.text().catch(() => r.statusText));
    return r.blob();
  },
  checkAuditLogExists: async (): Promise<boolean> => {
    const r = await fetch(`${BASE}/api/download/audit-log`, { method: "HEAD" });
    return r.ok;
  },
};

export function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Query keys ───────────────────────────────────────────────────────────────

export const QUERY_KEYS = {
  codebook: ["codebook"] as const,
  codebookMeta: ["codebook-meta"] as const,
  studies: ["studies"] as const,
  initialiseStatus: ["initialise-status"] as const,
  providers: ["providers"] as const,
  providerModels: (provider: string, baseUrl: string) => ["provider-models", provider, baseUrl] as const,
  mappings: (study: string, status?: string) =>
    ["mappings", study, status] as const,
  variableDetail: (study: string, variable: string) =>
    ["variable-detail", study, variable] as const,
  audit: (study: string) => ["audit", study] as const,
};

// ── TanStack Query hooks ─────────────────────────────────────────────────────

export function useCodebook() {
  return useQuery({
    queryKey: QUERY_KEYS.codebook,
    queryFn: api.getCodebook,
  });
}

export function useCodebookMeta() {
  return useQuery({
    queryKey: QUERY_KEYS.codebookMeta,
    queryFn: api.getCodebookMeta,
  });
}

export function useStudies() {
  return useQuery({
    queryKey: QUERY_KEYS.studies,
    queryFn: api.getStudies,
  });
}

export function useInitialiseStatus() {
  return useQuery({
    queryKey: QUERY_KEYS.initialiseStatus,
    queryFn: api.getInitialiseStatus,
  });
}

export function useProviders() {
  return useQuery({
    queryKey: QUERY_KEYS.providers,
    queryFn: api.getProviders,
  });
}

export function useProviderModels(provider: string, baseUrl: string, apiKey: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: QUERY_KEYS.providerModels(provider, baseUrl),
    queryFn: () => api.getProviderModels(provider, baseUrl, apiKey),
    enabled: enabled && !!baseUrl,
    staleTime: 30_000,
    retry: false,
  });
}

export function useMappings(study: string, status?: string) {
  return useQuery({
    queryKey: QUERY_KEYS.mappings(study, status),
    queryFn: () => api.getMappings(study, status),
    enabled: !!study,
  });
}

export function useVariableDetail(study: string, variable: string) {
  return useQuery({
    queryKey: QUERY_KEYS.variableDetail(study, variable),
    queryFn: () => api.getVariableDetail(study, variable),
    enabled: !!study && !!variable,
  });
}

export function useAudit(study: string, n?: number) {
  return useQuery({
    queryKey: QUERY_KEYS.audit(study),
    queryFn: () => api.getAudit(study, n),
    enabled: !!study,
  });
}

export function useUploadCodebook() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => api.uploadCodebook(file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.codebook });
      qc.invalidateQueries({ queryKey: QUERY_KEYS.codebookMeta });
    },
  });
}

export function useUploadStudy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: {
      name: string;
      variables: File;
      exampleData?: File;
      contextPdf?: File;
    }) => api.uploadStudy(args.name, args.variables, args.exampleData, args.contextPdf),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEYS.studies }),
  });
}

export function useDeleteStudy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => api.deleteStudy(name),
    onSuccess: () => qc.invalidateQueries({ queryKey: QUERY_KEYS.studies }),
  });
}

export function useTestConnection() {
  return useMutation({
    mutationFn: (config: AIConfig) => api.testConnection(config),
  });
}

export function useSaveMapping() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: { study: string; variable: string; body: MappingUpdateRequest }) =>
      api.saveMapping(args.study, args.variable, args.body),
    onSuccess: (_data, args) => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.mappings(args.study) });
      qc.invalidateQueries({
        queryKey: QUERY_KEYS.variableDetail(args.study, args.variable),
      });
    },
  });
}

export function useReopenMapping() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: { study: string; variable: string }) =>
      api.reopenMapping(args.study, args.variable),
    onSuccess: (_data, args) => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.mappings(args.study) });
      qc.invalidateQueries({
        queryKey: QUERY_KEYS.variableDetail(args.study, args.variable),
      });
    },
  });
}

export function useClearWorkspace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.clearWorkspace,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.studies });
      qc.invalidateQueries({ queryKey: QUERY_KEYS.initialiseStatus });
      qc.invalidateQueries({ queryKey: QUERY_KEYS.codebook });
    },
  });
}
