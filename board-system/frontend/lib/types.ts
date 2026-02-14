/** 引き取り者（Task 付箋をパーソナルに持っているユーザー） */
export interface TakenByUser {
  id: number;
  name: string;
  name_short: string;
}

/** ボード View 用: 配置 + 付箋本文 */
export interface PlacementWithNote {
  id: number;
  note_id: number;
  board_type: "MAIN" | "TASK" | "PERSONAL" | "MORNING";
  owner_id: number | null;
  lane: "INBOX" | "TODAY" | "DONE" | null;
  position_x: number | null;
  position_y: number | null;
  matrix_quadrant: number | null;
  sort_order: number;
  note_content: string;
  note_status: string;
  /** Personal のみ: タスクボードからコピーされた付箋か */
  is_from_task?: boolean;
  /** Task 用: 誰が引き取ったか */
  taken_by?: TakenByUser[];
  /** Task 用: 付箋の色 yellow=未引き取り green=引き取り中 grey=誰かがDone */
  task_color?: "yellow" | "green" | "grey";
}

export interface User {
  id: number;
  name: string;
  role: string | null;
}

export type LaneType = "INBOX" | "TODAY" | "DONE";
