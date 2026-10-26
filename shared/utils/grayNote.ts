/**
 * 付箋がグレー（完了・アーカイブ等）判定されるかチェックする共通ユーティリティ。
 * gray, is_gray, isGray のプロパティの揺れを吸収して真偽値を返します。
 */
export function isGrayNote(note: any): boolean {
    return Boolean(note?.gray || note?.is_gray || note?.isGray);
}
