export const LEGACY_POSTIT_BOARD_URL =
  process.env.NEXT_PUBLIC_LEGACY_BOARD_URL || "http://localhost:3000";
export const LEGACY_POSTIT_BOARD_ID = "wl";

type LegacyPostitNote = {
  id: string;
  text: string;
  gray?: boolean;
  dueDate?: string;
};

export type PostitImportNote = {
  id: string;
  text: string;
  due_date: string | null;
};

/**
 * 旧付箋ボードから、取り込み対象だけを API の入力形式で取得する。
 * 手動取り込みと定期取り込みで同じ変換規則を必ず使うための境界。
 */
export async function fetchLegacyPostitNotes(): Promise<PostitImportNote[]> {
  const response = await fetch(
    `${LEGACY_POSTIT_BOARD_URL}/api/boards/${LEGACY_POSTIT_BOARD_ID}/notes`
  );
  if (!response.ok) {
    throw new Error("付箋ボードの取得に失敗しました");
  }

  const data = (await response.json()) as { notes?: LegacyPostitNote[] };
  return (data.notes ?? [])
    .filter((note) => !note.gray)
    .map((note) => ({
      id: String(note.id),
      text: note.text || "",
      due_date: note.dueDate ?? null,
    }));
}
