export type ConnectionState = "checking" | "connected" | "disconnected";
export type StageState = "pending" | "processing" | "success" | "failed";

export type PipelineStage = {
  id: string;
  label: string;
  state: StageState;
};

export type HealthResponse = {
  status?: string;
  blockchain?: { connected?: boolean; status?: string };
  components?: Record<string, string>;
  [key: string]: unknown;
};

export type Candidate = {
  post_id?: string;
  similarity_score?: number;
  image_path?: string;
  metadata?: Record<string, unknown>;
};

export type PipelineResponse = {
  pipeline_id?: string;
  search?: {
    search_id?: string;
    provider?: string;
    candidate_count?: number;
    results?: Candidate[];
  };
  candidate?: Candidate;
  match?: {
    match?: boolean;
    confidence?: number;
    face_similarity?: number;
    image_similarity?: number | null;
    metadata_consistency?: number | null;
    threshold?: number;
  };
  evidence?: Record<string, unknown>;
  evidence_path?: string;
  evidence_hash?: string;
  blockchain?: {
    transaction_hash?: string;
    block_number?: number;
    timestamp?: string;
    contract_address?: string;
    verifier?: string;
    status?: number;
  };
  reverification?: {
    verified?: boolean;
    status?: string;
    local_hash?: string;
    blockchain_hash?: string;
    reason?: string;
  };
  [key: string]: unknown;
};

export type ApiError = Error & { status?: number };

export type VerificationResponse = {
  verified?: boolean;
  status?: string;
  local_hash?: string;
  blockchain_hash?: string;
  reason?: string;
  [key: string]: unknown;
};
