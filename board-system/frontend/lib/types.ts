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
}

export interface User {
  id: number;
  name: string;
  role: string | null;
}

export type LaneType = "INBOX" | "TODAY" | "DONE";
