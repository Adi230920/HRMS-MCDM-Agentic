"use client";

import { useEffect, useState } from "react";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Rating = "NOT_DEMONSTRATED" | "PARTIAL" | "STRONG";
export type Rec = "ADVANCE" | "REVIEW" | "DO_NOT_ADVANCE";
export type AgentName = "TECHNICAL" | "DELIVERY" | "COLLABORATION";

export interface Turn {
  id: string;
  speaker: "INTERVIEWER" | "CANDIDATE";
  text: string;
}

export interface Claim {
  id: string;
  text: string;
  category: "technical" | "delivery" | "collaboration";
  resume_quote: string;
}

export interface Evidence {
  source: "resume" | "transcript";
  quote: string;
  verified: boolean;
}

export interface CriterionRating {
  criterion: string;
  rating: Rating;
  evidence: Evidence[];
}

export interface ClaimFinding {
  claim_id: string;
  status: "SUPPORTED" | "CONTRADICTED" | "UNVERIFIED";
  evidence: Evidence[];
}

export interface AgentEval {
  agent?: AgentName;
  ratings: CriterionRating[];
  claim_findings: ClaimFinding[];
  recommendation: Rec;
  whisper?: string;
  reasoning?: string;
  violations?: string[];
}

export interface Sample {
  id: string;
  label: string;
  expected: string;
  filename: string;
  jd: string;
  resume?: string;
  transcript?: string;
  candidate_name?: string;
  resume_preview?: string;
}

export interface CreateRunRequest {
  jd: string;
  resume: string;
  transcript: string;
  candidate_name?: string;
}

export interface CreateRunResponse {
  run_id: string;
  status: string;
  cached: boolean;
  decision?: string;
  council_score?: number;
}

export interface LLMCallRecord {
  role: string;
  provider: string;
  model: string;
  tokens: number;
  latency: number;
  error?: string | null;
}

export interface RunDetail {
  id: string;
  status: "PROCESSING" | "COMPLETED" | "FAILED";
  created_at: string;
  decision?: string | null;
  council_score?: number | null;
  base_score?: number | null;
  quorum?: boolean | null;
  veto?: boolean | null;
  veto_signals?: string[];
  unresolved?: boolean | null;
  aar?: boolean | null;
  error?: string | null;
  inputs: {
    jd: string;
    resume_redacted: string;
    transcript_redacted: string;
  };
  artifacts: {
    gate?: Record<string, unknown>;
    evals?: Record<string, AgentEval>;
    points?: Array<unknown>;
    chair?: string;
    trace?: Array<[string, number]>;
    revisions?: Array<unknown>;
    warnings?: string[];
    [key: string]: unknown;
  };
  llm_calls: LLMCallRecord[];
  reviews: Array<{
    id: number;
    decision: string;
    reviewer: string;
    notes: string;
    created_at: string;
  }>;
}

export interface SSEEventData {
  event: string;
  data: Record<string, unknown>;
  timestamp?: number;
}

export async function getSamples(): Promise<Sample[]> {
  const res = await fetch(`${API_BASE}/api/samples`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to fetch samples: ${res.statusText}`);
  }
  return res.json();
}

export async function createRun(
  payload: CreateRunRequest,
  mock = false
): Promise<CreateRunResponse> {
  const url = `${API_BASE}/api/runs${mock ? "?mock=true" : ""}`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({}));
    throw new Error(errorBody.detail || `Run creation failed (${res.status})`);
  }

  return res.json();
}

export async function getRun(runId: string): Promise<RunDetail> {
  const res = await fetch(`${API_BASE}/api/runs/${runId}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load run: ${res.statusText}`);
  }
  return res.json();
}

export interface StageInfo {
  id: string;
  name: string;
  description: string;
  status: "idle" | "running" | "completed" | "failed";
  duration?: number;
  meta?: Record<string, unknown>;
}

const INITIAL_STAGES: StageInfo[] = [
  {
    id: "ingest",
    name: "Ingestion & Extraction",
    description: "PII redaction, transcript parsing, and verifiable claim extraction",
    status: "idle",
  },
  {
    id: "technical",
    name: "Technical Evaluator",
    description: "Domain competency and technical claim verification",
    status: "idle",
  },
  {
    id: "delivery",
    name: "Delivery Evaluator",
    description: "Execution velocity, ownership, and scope assessment",
    status: "idle",
  },
  {
    id: "collaboration",
    name: "Collaboration Evaluator",
    description: "Teamwork, empathy, and communication assessment",
    status: "idle",
  },
  {
    id: "conflicts",
    name: "Conflict Detection",
    description: "Multi-agent disparity and contested evidence analysis",
    status: "idle",
  },
  {
    id: "debate",
    name: "Adversarial Debate",
    description: "Moderated cross-examination of disputed points",
    status: "idle",
  },
  {
    id: "gate",
    name: "Deterministic Gate",
    description: "Rule-based score aggregation, veto checks, and quorum validation",
    status: "idle",
  },
  {
    id: "chair",
    name: "Executive Chair Summary",
    description: "Final decision synthesis and recommendation prose",
    status: "idle",
  },
];

export function useRunEvents(runId: string | null) {
  const [events, setEvents] = useState<SSEEventData[]>([]);
  const [stages, setStages] = useState<StageInfo[]>(INITIAL_STAGES);
  const [llmCallCount, setLlmCallCount] = useState<number>(0);
  const [isDone, setIsDone] = useState<boolean>(false);
  const [isFailed, setIsFailed] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [runData, setRunData] = useState<RunDetail | null>(null);

  useEffect(() => {
    if (!runId) return;

    // Reset state
    setStages(INITIAL_STAGES.map((s, idx) => ({
      ...s,
      status: idx === 0 ? "running" : "idle",
    })));
    setEvents([]);
    setLlmCallCount(0);
    setIsDone(false);
    setIsFailed(false);
    setError(null);
    setRunData(null);

    const eventSource = new EventSource(`${API_BASE}/api/runs/${runId}/events`);

    const updateStage = (
      stageId: string,
      status: StageInfo["status"],
      duration?: number,
      meta?: Record<string, unknown>
    ) => {
      setStages((prev) =>
        prev.map((s) =>
          s.id === stageId
            ? { ...s, status, ...(duration !== undefined ? { duration } : {}), ...(meta ? { meta } : {}) }
            : s
        )
      );
    };

    const handleEventPayload = (eventName: string, data: Record<string, unknown>) => {
      setEvents((prev) => [...prev, { event: eventName, data }]);

      switch (eventName) {
        case "ingest_completed":
          updateStage("ingest", "completed", Number(data.elapsed) || 0, data);
          setLlmCallCount((c) => Math.max(c, 1));
          updateStage("technical", "running");
          updateStage("delivery", "running");
          updateStage("collaboration", "running");
          break;

        case "agent_completed": {
          const agent = String(data.agent || "").toLowerCase();
          if (agent === "technical") {
            updateStage("technical", "completed", Number(data.elapsed) || 0, data);
          } else if (agent === "delivery") {
            updateStage("delivery", "completed", Number(data.elapsed) || 0, data);
          } else if (agent === "collaboration") {
            updateStage("collaboration", "completed", Number(data.elapsed) || 0, data);
          }
          setLlmCallCount((c) => c + 1);
          break;
        }

        case "agent_failed": {
          const agent = String(data.agent || "").toLowerCase();
          if (agent === "technical") {
            updateStage("technical", "failed", Number(data.elapsed) || 0, data);
          } else if (agent === "delivery") {
            updateStage("delivery", "failed", Number(data.elapsed) || 0, data);
          } else if (agent === "collaboration") {
            updateStage("collaboration", "failed", Number(data.elapsed) || 0, data);
          }
          break;
        }

        case "conflicts_detected":
          updateStage("conflicts", "completed", Number(data.elapsed) || 0, data);
          if (Number(data.points_count) > 0) {
            updateStage("debate", "running");
          } else {
            updateStage("debate", "completed", 0, { skipped: true });
            updateStage("gate", "running");
          }
          break;

        case "debate_completed":
          updateStage("debate", "completed", Number(data.elapsed) || 0, data);
          setLlmCallCount((c) => c + 1);
          updateStage("gate", "running");
          break;

        case "gate_completed":
          updateStage("gate", "completed", Number(data.elapsed) || 0, data);
          updateStage("chair", "running");
          break;

        case "chair_completed":
          updateStage("chair", "completed", Number(data.elapsed) || 0, data);
          setLlmCallCount((c) => c + 1);
          break;

        case "done":
          setStages((prev) =>
            prev.map((s) => ({
              ...s,
              status: s.status === "failed" ? "failed" : "completed",
            }))
          );
          setIsDone(true);
          // Fetch final run record
          getRun(runId)
            .then((res) => {
              setRunData(res);
              if (res.llm_calls && res.llm_calls.length > 0) {
                setLlmCallCount(res.llm_calls.length);
              }
            })
            .catch((e) => console.error("Failed fetching completed run detail:", e));
          eventSource.close();
          break;

        case "error":
          setIsFailed(true);
          setError(String(data.error || "Execution failed"));
          eventSource.close();
          break;
      }
    };

    // Standard SSE listeners for each named event emitted by backend
    const eventNames = [
      "ingest_completed",
      "agent_completed",
      "agent_failed",
      "conflicts_detected",
      "debate_completed",
      "gate_completed",
      "chair_completed",
      "done",
      "error",
    ];

    eventNames.forEach((evName) => {
      eventSource.addEventListener(evName, (e: MessageEvent) => {
        try {
          const parsed = JSON.parse(e.data);
          handleEventPayload(evName, parsed);
        } catch (err) {
          console.error(`Failed parsing SSE event ${evName}:`, err);
        }
      });
    });

    eventSource.onerror = () => {
      // Check if finished via polling run status
      getRun(runId)
        .then((res) => {
          if (res.status === "COMPLETED") {
            setStages((prev) =>
              prev.map((s) => ({
                ...s,
                status: s.status === "failed" ? "failed" : "completed",
              }))
            );
            setIsDone(true);
            setRunData(res);
            if (res.llm_calls) setLlmCallCount(res.llm_calls.length);
            eventSource.close();
          } else if (res.status === "FAILED") {
            setIsFailed(true);
            setError(res.error || "Run failed");
            eventSource.close();
          }
        })
        .catch(() => {
          // Keep waiting or close if needed
        });
    };

    return () => {
      eventSource.close();
    };
  }, [runId]);

  return {
    events,
    stages,
    llmCallCount,
    isDone,
    isFailed,
    error,
    runData,
  };
}

