"use client";

import type { ReactNode } from "react";

const URL_REGEX = /(https?:\/\/[^\s<>\[\]()]+)/gi;
const MARKDOWN_LINK_REGEX = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/gi;
const URL_DISPLAY_MAX = 40;

function shortenUrl(url: string): string {
  return url.length <= URL_DISPLAY_MAX ? url : url.slice(0, URL_DISPLAY_MAX - 1) + "…";
}

function createLink(url: string, label: string, key: string): ReactNode {
  return (
    <a
      key={key}
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      title={url}
      className="text-blue-600 underline hover:text-blue-800"
      onClick={(event) => event.stopPropagation()}
    >
      {label}
    </a>
  );
}

function linkifyPlainText(text: string, keyPrefix: string): ReactNode[] {
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let keyIndex = 0;
  const regex = new RegExp(URL_REGEX.source, "gi");
  let match: RegExpExecArray | null;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(<span key={`${keyPrefix}-text-${keyIndex++}`}>{text.slice(lastIndex, match.index)}</span>);
    }
    parts.push(createLink(match[0], shortenUrl(match[0]), `${keyPrefix}-link-${keyIndex++}`));
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push(<span key={`${keyPrefix}-text-${keyIndex++}`}>{text.slice(lastIndex)}</span>);
  }
  return parts.length ? parts : [text];
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
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let keyIndex = 0;
  const regex = new RegExp(MARKDOWN_LINK_REGEX.source, "gi");
  let match: RegExpExecArray | null;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(...linkifyPlainText(text.slice(lastIndex, match.index), `before-${keyIndex++}`));
    }
    parts.push(createLink(match[2], match[1], `markdown-link-${keyIndex++}`));
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push(...linkifyPlainText(text.slice(lastIndex), `after-${keyIndex++}`));
  }
  return (
    <span className={className}>
      {parts.length ? parts : linkifyPlainText(text, "all")}
    </span>
  );
}
