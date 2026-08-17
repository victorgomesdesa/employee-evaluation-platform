import type { Leader, Subordinate } from "../types/hierarchy";

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(path, options);

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getLeaders(signal?: AbortSignal): Promise<Leader[]> {
  return request<Leader[]>("/api/leaders", { signal });
}

function protectedRequest<T>(
  path: string,
  actingLeaderId: number,
  signal?: AbortSignal,
): Promise<T> {
  return request<T>(path, {
    signal,
    headers: {
      "X-Leader-Id": String(actingLeaderId),
    },
  });
}

export function getSubordinates(
  actingLeaderId: number,
  signal?: AbortSignal,
): Promise<Subordinate[]> {
  return protectedRequest<Subordinate[]>(
    "/api/me/subordinates",
    actingLeaderId,
    signal,
  );
}
