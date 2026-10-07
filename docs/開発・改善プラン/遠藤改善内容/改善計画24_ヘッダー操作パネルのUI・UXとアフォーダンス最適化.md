# 改善計画24: ヘッダー操作パネルのUI/UX・アフォーダンス最適化

## 1. 概要・目的

現在タスクボード上部に配置されている「付箋取り込み・ゴミ箱・パーソナルコピー・チーム一括コピー」の操作パネルにおいて、**ゴミ箱やコピー先バッジはクリック操作を受け付けず、ドラッグ＆ドロップ（D&D）のドロップターゲットとしてのみ機能します**。

従来の「ボタン風」の見た目や指マークカーソル（`cursor-pointer`）、クリック時の押し込みエフェクト（`active:scale-95`）はユーザーに「クリックで動作する」という誤解を与える原因となるため、これらを完全に排除します。

本計画では、純粋なドロップターゲット（Drop Zone）としてのアフォーダンスに特化し、通常時は落ち着いた枠エリアとして表示しつつ、**ドラッグオーバー時（付箋を重ねた瞬間）にのみ強力に強調・発光するフィードバック**へ刷新します。

---

## 2. 主な改善ポイント

### 2.1 クリック用属性・エフェクトの完全排除 (D&D Exclusive)

* **誤解を招くスタイル・属性の削除**:
  * クリック指マーク（`cursor-pointer`）➔ 平時は通常のカーソル（`cursor-default`）に変更。
  * クリック押下エフェクト（`active:scale-95`）およびホバー浮き上がり（`hover:-translate-y-0.5`）を削除。
  * 誤ったボタン認識を防ぐため、`role="button"` や `tabIndex={0}` 等のボタン属性を削除。
* **クリック可能なボタンとの明確な差別化**:
  * 「付箋ボードから取り込む」ボタンのみクリック操作が存在するため、これだけに `cursor-pointer` や `active:scale-95` を保持し、ドロップターゲットエリアとの視覚的・操作的違いを明確にします。

### 2.2 ドロップターゲット専用アフォーダンスの強化 (Interactive Drop Zone)

* **Drag Over エフェクトの強調**: 付箋をドラッグしてバッジやゴミ箱の上に重ねた瞬間（`activeDragTarget === id`）にのみ、背景変化・拡大（`scale-105`）・鮮やかなリング発光（`ring-2`）が働き、「ここにドロップして割り当て/削除できる」ことを即座に知らしめます。
* **チラつき（Flicker）防止対策**: バッジ内のテキストやアイコン子要素に `[&>*]:pointer-events-none` を設定し、`dragleave` の誤発火によるエフェクトのチラつきを排除します。
* **ドラッグキャンセル・離脱時のエッジケースケア**: ウィンドウ外離脱時やドラッグキャンセル時にもハイライト表示が残らないよう、全域での離脱・キャンセルイベント（`onDragEnd` / `onDragLeave`）時にターゲット状態を確実にリセットします。

### 2.3 ヒットエリア・レスポンシブ・スケーラビリティ対応

* **サイズ・余白の拡張**: バッジ・ゴミ箱の内部余白を十分確保（`px-3.5 py-1.5`、最小高さ 36px）し、ドラッグ時のドロップ判定エリアを拡大。
* **全ブラウザ対応スリムスクロールバー**: メンバー数やチーム数が多い環境でもタスクボードキャンバスを圧迫しないよう、最大高さ制限（`max-h-28`）と Chrome/Safari/Edge/Firefox 対応のスリムスクロールバーを採用します。

---

## 3. 影響範囲・対象ファイル

* `frontend/app/taskboard/page.tsx`（またはパネルを保持する親コンポーネント）
* `frontend/app/components/OneLineInput.tsx` / `Nav.tsx`（関連コンポーネント）
* パネル表示用スタイリング・コンポーネントファイル

---

## 4. コンポーネント実装コード（D&D専用・完全確定版）

```tsx
import React, { useState, useCallback } from "react";

export interface Member {
  id: number;
  name: string;
}

export interface Team {
  id: number;
  name: string;
  memberCount: number;
}

interface OperationPanelProps {
  members: Member[];
  teams: Team[];
  autoImport: boolean;
  isImporting?: boolean;
  onAutoImportChange: (checked: boolean) => void;
  onImportClick: () => void;
  onTrashDrop: (e: React.DragEvent) => void;
  onMemberDrop: (memberId: number, e: React.DragEvent) => void;
  onTeamDrop: (teamId: number, e: React.DragEvent) => void;
}

export const OperationPanel: React.FC<OperationPanelProps> = ({
  members,
  teams,
  autoImport,
  isImporting = false,
  onAutoImportChange,
  onImportClick,
  onTrashDrop,
  onMemberDrop,
  onTeamDrop,
}) => {
  const [activeDragTarget, setActiveDragTarget] = useState<string | null>(null);

  // ドラッグ進入・移動時の処理
  const handleDragOver = useCallback((id: string, e: React.DragEvent) => {
    e.preventDefault();
    setActiveDragTarget((prev) => (prev !== id ? id : prev));
  }, []);

  // ドラッグ離脱・終了時の全域リセット処理
  const resetDragTarget = useCallback(() => {
    setActiveDragTarget(null);
  }, []);

  const handleDrop = useCallback(
    (id: string, callback: (e: React.DragEvent) => void, e: React.DragEvent) => {
      e.preventDefault();
      resetDragTarget();
      callback(e);
    },
    [resetDragTarget]
  );

  return (
    <div
      onDragLeave={resetDragTarget}
      onDragEnd={resetDragTarget}
      className="flex flex-col gap-3 p-3.5 bg-white/90 backdrop-blur-md rounded-2xl border border-zinc-200/80 shadow-sm"
    >
      {/* 上段: 操作アクション & ゴミ箱 */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-zinc-100">
        <div className="flex flex-wrap items-center gap-3">
          {/* クリック動作のあるボタン（指マーク＆押下エフェクトあり） */}
          <button
            type="button"
            onClick={onImportClick}
            disabled={isImporting}
            className="flex items-center gap-1.5 px-4 py-2 bg-[var(--primary)] hover:bg-[var(--primary-hover)] disabled:opacity-50 text-white text-sm font-bold rounded-xl shadow-sm hover:shadow transition-all active:scale-95 cursor-pointer"
          >
            {isImporting ? (
              <span className="flex items-center gap-1.5">
                <span className="animate-spin text-xs">🌀</span>
                <span>取り込み中…</span>
              </span>
            ) : (
              <span>付箋ボードから取り込む</span>
            )}
          </button>

          <label className="flex items-center gap-2 cursor-pointer text-sm font-medium text-zinc-700 hover:text-zinc-900 select-none">
            <input
              type="checkbox"
              checked={autoImport}
              onChange={(e) => onAutoImportChange(e.target.checked)}
              className="w-4 h-4 rounded border-zinc-300 text-[var(--primary)] focus:ring-[var(--primary)] cursor-pointer"
            />
            <span>自動で取り込む（5分ごと・AI判定）</span>
          </label>
        </div>

        {/* ゴミ箱（D&D専用ターゲット: クリック用属性・カーソル・ボタンエフェクト排除） */}
        <div
          aria-label="ゴミ箱エリア。付箋をここにドロップして削除"
          onDragOver={(e) => handleDragOver("trash", e)}
          onDragLeave={resetDragTarget}
          onDrop={(e) => handleDrop("trash", onTrashDrop, e)}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-semibold transition-all select-none cursor-default border [&>*]:pointer-events-none ${
            activeDragTarget === "trash"
              ? "bg-rose-100 border-rose-400 text-rose-700 ring-2 ring-rose-400 scale-105 shadow-md"
              : "bg-rose-50/60 border-rose-200/80 text-rose-600"
          }`}
        >
          <span className="text-base">🗑️</span>
          <span>ゴミ箱</span>
        </div>
      </div>

      {/* 中段: パーソナルコピー（D&D専用ターゲット） */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-2.5">
        <span className="text-sm font-semibold text-zinc-600 whitespace-nowrap shrink-0">
          パーソナルコピー:
        </span>
        {/* max-h-28 + スリムスクロールバー対応 */}
        <div className="flex flex-wrap gap-2 max-h-28 overflow-y-auto pr-1 w-full [scrollbar-width:thin] [scrollbar-color:theme(colors.zinc.200)_transparent] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:bg-zinc-200 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-transparent">
          {members.map((m) => {
            const targetId = `member-${m.id}`;
            const isHovered = activeDragTarget === targetId;
            return (
              <div
                key={m.id}
                aria-label={`${m.name} のパーソナルボードへ付箋をドロップしてコピー`}
                onDragOver={(e) => handleDragOver(targetId, e)}
                onDragLeave={resetDragTarget}
                onDrop={(e) => handleDrop(targetId, (e) => onMemberDrop(m.id, e), e)}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-sm font-medium transition-all select-none cursor-default border [&>*]:pointer-events-none ${
                  isHovered
                    ? "bg-sky-100 border-sky-400 text-sky-800 ring-2 ring-sky-400 scale-105 shadow-md"
                    : "bg-zinc-50 border-zinc-200 text-zinc-700"
                }`}
              >
                <span className="flex items-center justify-center w-5 h-5 rounded-full bg-zinc-200 text-zinc-600 text-xs font-bold">
                  {m.name.charAt(0)}
                </span>
                <span>{m.name}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 下段: チーム一括コピー（D&D専用ターゲット） */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-2.5 pt-1 border-t border-zinc-100/60">
        <span className="text-sm font-semibold text-zinc-600 whitespace-nowrap shrink-0">
          チーム一括コピー:
        </span>
        <div className="flex flex-wrap gap-2 max-h-28 overflow-y-auto pr-1 w-full [scrollbar-width:thin] [scrollbar-color:theme(colors.zinc.200)_transparent] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-thumb]:bg-zinc-200 [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-transparent">
          {teams.map((t) => {
            const targetId = `team-${t.id}`;
            const isHovered = activeDragTarget === targetId;
            return (
              <div
                key={t.id}
                aria-label={`${t.name} チーム所属メンバー全員へ一括コピー（${t.memberCount}名）`}
                onDragOver={(e) => handleDragOver(targetId, e)}
                onDragLeave={resetDragTarget}
                onDrop={(e) => handleDrop(targetId, (e) => onTeamDrop(t.id, e), e)}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-sm font-semibold transition-all select-none cursor-default border [&>*]:pointer-events-none ${
                  isHovered
                    ? "bg-indigo-100 border-indigo-500 text-indigo-900 ring-2 ring-indigo-400 scale-105 shadow-md"
                    : "bg-indigo-50/70 border-indigo-200 text-indigo-700"
                }`}
              >
                <span className="text-xs">👥</span>
                <span>{t.name}</span>
                <span className="text-xs font-normal text-indigo-500 bg-indigo-100/80 px-1.5 py-0.5 rounded-full">
                  {t.memberCount}名
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

```

---

## 5. 検証手順

1. **ボタンとドロップエリアの識別性の確認**:

* 「付箋ボードから取り込む」ボタンのみマウスカーソルが指マーク（`cursor-pointer`）になり、クリック時に押下感があることを確認。

* ゴミ箱・メンバーバッジ・チームバッジは指マークにならず（`cursor-default`）、クリックしても押下エフェクトが発生しないことを確認。

1. **ドラッグ＆ドロップ（DnD）動作の確認**:

* 付箋カードをドラッグしてゴミ箱・メンバーバッジ・チームバッジへ重ねた際、対象エリアが即座に拡大・発光してドロップ受け入れ状態になることを確認。

* バッジ内のテキストやアイコン上にカーソルが重なっても発光がチラつかないことを確認。

* ドロップ時にそれぞれのドロップ処理（削除・パーソナルコピー・チーム一括コピー）が正しく実行されることを確認。
