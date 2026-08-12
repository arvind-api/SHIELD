export interface User {
  id: number;
  email: string;
  created_at: string;
}

// --- Auth -------------------------------------------------------------
// Mirrors backend/app/schemas/auth.py 1:1.

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

// --- Email Analyzer -------------------------------------------------------
// Mirrors backend/app/schemas/email_analyzer.py 1:1.

export interface EmailAnalyzeRequest {
  raw_email: string;
}

export interface EmailAnalysisResult {
  tone: string;
  intent: string;
  phishing_signals: string[];
  risk_score: number;
  risk_level: "low" | "medium" | "high";
  suggested_reply: string;
}

export interface EmailAnalyzeResponse extends EmailAnalysisResult {
  id: number;
}

// --- Guardian Scam Scanner -------------------------------------------------
// Mirrors backend/app/schemas/guardian_scanner.py 1:1.

export interface ScanRequest {
  input_text: string;
}

export interface ScamScanResult {
  risk_level: "low" | "medium" | "high";
  risk_score: number;
  category: string;
  red_flags: string[];
  reasoning: string;
}

export interface ScanResponse extends ScamScanResult {
  id: number;
}
