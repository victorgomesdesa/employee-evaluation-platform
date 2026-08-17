import type { Leader, Subordinate } from "../types/hierarchy";
import type {
  CreateEvaluationRequest,
  EvaluationQuestion,
  EvaluationResponse,
} from "../types/evaluation";

export class ApiError extends Error {
  constructor(public readonly status: number) {
    super(`API request failed with status ${status}`);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(path, options);

  if (!response.ok) {
    throw new ApiError(response.status);
  }

  return response.json() as Promise<T>;
}

export function getLeaders(signal?: AbortSignal): Promise<Leader[]> {
  return request<Leader[]>("/api/leaders", { signal });
}

function protectedRequest<T>(
  path: string,
  actingLeaderId: number,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("X-Leader-Id", String(actingLeaderId));

  return request<T>(path, {
    ...options,
    headers,
  });
}

export function getSubordinates(
  actingLeaderId: number,
  signal?: AbortSignal,
): Promise<Subordinate[]> {
  return protectedRequest<Subordinate[]>(
    "/api/me/subordinates",
    actingLeaderId,
    { signal },
  );
}

export function getEvaluationQuestions(
  signal?: AbortSignal,
): Promise<EvaluationQuestion[]> {
  return request<EvaluationQuestion[]>("/api/evaluation/questions", { signal });
}

export function createEvaluation(
  actingLeaderId: number,
  evaluation: CreateEvaluationRequest,
): Promise<EvaluationResponse> {
  return protectedRequest<EvaluationResponse>(
    "/api/evaluations",
    actingLeaderId,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(evaluation),
    },
  );
}
