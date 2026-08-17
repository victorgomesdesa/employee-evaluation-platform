export interface Leader {
  id: number;
  name: string;
  positionName: string;
}

export type Relationship = "direct" | "indirect";

export interface Subordinate {
  id: number;
  name: string;
  email: string;
  positionName: string;
  relationship: Relationship;
  depth: number;
}
