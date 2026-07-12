export interface EvidenceItem {
  chunk_id: string;
  doc_id: string;
  text: string;
  score: number;
}

export interface QueryResponse {
  question: string;
  answer: string;
  is_fully_grounded: boolean;
  was_rejected: boolean;
  hallucinated_citations: string[];
  evidence: EvidenceItem[];
  latency_ms: number;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  files_accepted: number;
  total_documents: number;
  total_chunks: number;
}
