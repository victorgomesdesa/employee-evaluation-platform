export type Score = 1 | 2 | 3 | 4;

export interface EvaluationQuestion {
  id: number;
  text: string;
  weight: number;
  displayOrder: number;
}

export interface EvaluationAnswerInput {
  questionId: number;
  score: Score;
}

export interface CreateEvaluationRequest {
  employeeId: number;
  answers: EvaluationAnswerInput[];
}

export interface EvaluationAnswerResponse {
  questionId: number;
  score: Score;
  weight: number;
}

export interface EvaluationResponse {
  id: number;
  employeeId: number;
  evaluatorId: number;
  weekReference: string;
  createdAt: string;
  totalScore: string;
  answers: EvaluationAnswerResponse[];
}

export interface PrimaryEvaluationAnswer {
  questionId: number;
  questionText: string;
  score: Score;
  weight: number;
}

export interface EvaluationAuthor {
  id: number;
  name: string;
  positionName: string;
}

export interface PrimaryEvaluation {
  id: number;
  employeeId: number;
  evaluator: EvaluationAuthor;
  weekReference: string;
  createdAt: string;
  totalScore: string;
  answers: PrimaryEvaluationAnswer[];
}
