export interface CodebookVariable {
  variable_name: string;
  description: string;
  dType?: string;
  unit?: string;
  categories?: string;
  unit_example?: string;
}

export interface StudyVariable {
  variable_name: string;
  description?: string;
  target_recommendations?: string[];
  target_distances?: number[];
  PID_recommendations?: string[];
  PID_distances?: number[];
  date_recommendations?: string[];
  date_distances?: number[];
}

export interface Study {
  name: string;
  variable_count: number;
  has_example_data: boolean;
  has_context_pdf: boolean;
  status: "uploaded" | "initialised" | "mapping" | "complete";
}

export interface MappingRecord {
  study_var: string;
  codebook_var?: string;
  confidence?: string;
  notes?: string;
  marked: "To do" | "Successfully mapped" | "Marked to reconsider" | "Marked unmappable";
  transformation_instructions?: string;
  transformation_type?: "Direct" | "Categorical";
  source_dtype?: string;
  target_dtype?: string;
  patient_id_var?: string;
  date_var?: string;
}

export type AIProviderId = "ollama" | "vllm" | "openai" | "anthropic" | "azure_openai";

export interface ProviderSlot {
  provider: AIProviderId;
  model: string;
  api_key?: string;
  base_url?: string;
  azure_api_version?: string;
  azure_deployment?: string;
}

export interface AIConfig {
  chat: ProviderSlot;
  embedding?: ProviderSlot | null;
  request_timeout: number;
}

export interface VariableDraft {
  variable_name: string;
  selected_codebook_var: string | null;
  marking: MappingRecord["marked"];
  notes: string;
  transformation_type: "Direct" | "Categorical";
  transformation_instructions: string;
  source_dtype: string;
  target_dtype: string;
  patient_id_var: string | null;
  date_var: string | null;
}
