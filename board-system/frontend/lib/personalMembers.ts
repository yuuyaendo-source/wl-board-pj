/** パーソナルボード メンバー（slug → owner_id, 表示名）。API の owner_id は 1〜7 で対応 */
export const PERSONAL_MEMBERS = [
  { slug: "hori" as const, ownerId: 1, name: "堀 高喜" },
  { slug: "fukuyama" as const, ownerId: 2, name: "福山 一道" },
  { slug: "kobayashi" as const, ownerId: 3, name: "小林 康三" },
  { slug: "thang" as const, ownerId: 4, name: "ブイクエット タン" },
  { slug: "asakawa" as const, ownerId: 5, name: "浅川 久司" },
  { slug: "endo" as const, ownerId: 6, name: "遠藤 悠矢" },
  { slug: "hayashida" as const, ownerId: 7, name: "林田 康佑" },
] as const;

export type PersonalSlug = (typeof PERSONAL_MEMBERS)[number]["slug"];

export function getMemberBySlug(slug: string): { ownerId: number; name: string } | null {
  const m = PERSONAL_MEMBERS.find((x) => x.slug === slug);
  return m ? { ownerId: m.ownerId, name: m.name } : null;
}
