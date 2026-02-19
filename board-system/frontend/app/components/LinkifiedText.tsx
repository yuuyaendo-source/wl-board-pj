"use client";

import type { ReactElement } from "react";

const URL_REGEX = /(https?:\/\/[^\s<>\[\]()]+)/gi;
const URL_DISPLAY_MAX = 40;

function shortenUrl(url: string): string {
  return url.length <= URL_DISPLAY_MAX ? url : url.slice(0, URL_DISPLAY_MAX - 1) + "…";
}

/**
 * テキスト中の URL をリンク化して表示する。長い URL は省略表示（title で全文）。
 */
export default function LinkifiedText({
  text,
  className,
}: {
  text: string | null | undefined;
  className?: string;
}) {
  if (text == null || text === "") return null;
  const parts: ReactElement[] = [];
  let lastIndex = 0;
  let keyIndex = 0;
  let m;
  const re = new RegExp(URL_REGEX.source, "gi");
  while ((m = re.exec(text)) !== null) {
    if (m.index > lastIndex) {
      parts.push(<span key={`t-${keyIndex++}`}>{text.slice(lastIndex, m.index)}</span>);
    }
    const url = m[0];
    const display = shortenUrl(url);
    parts.push(
      <a
        key={`a-${keyIndex++}`}
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        title={url}
        className="text-blue-600 underline hover:text-blue-800"
        onClick={(e) => e.stopPropagation()}
      >
        {display}
      </a>
    );
    lastIndex = re.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push(<span key={`t-${keyIndex++}`}>{text.slice(lastIndex)}</span>);
  }
  return (
    <span className={className}>
      {parts.length ? parts : text}
    </span>
  );
}
