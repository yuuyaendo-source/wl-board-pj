"use client";

import type { ReactNode } from "react";
// 共通ユーティリティからインポート
import { parseTextWithLinks } from "@shared/utils/linkify";

/**
 * テキスト中の URL や Markdown リンクを <a> タグ化して表示する。
 */
export default function LinkifiedText({
  text,
  className,
}: {
  text: string | null | undefined;
  className?: string;
}) {
  if (text == null || text === "") return null;

  // utils/linkify.ts でテキストとリンクのパーツ配列へ分解
  const parts = parseTextWithLinks(text);

  return (
    <span className={className}>
      {parts.map((part, index) => {
        if (part.type === "link" && part.url) {
          return (
            <a
              key={index}
              href={part.url}
              target="_blank"
              rel="noopener noreferrer"
              title={part.url}
              className="text-blue-600 underline hover:text-blue-800"
              onClick={(event) => event.stopPropagation()}
            >
              {part.content}
            </a>
          );
        }
        return <span key={index}>{part.content}</span>;
      })}
    </span>
  );
}