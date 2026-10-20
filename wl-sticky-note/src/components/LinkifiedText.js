"use client";

import { parseTextWithLinks } from "@shared/utils/linkify";

/**
 * テキスト中の URL（http/https）および Markdown 形式リンクを <a> タグでリンク化して表示する。
 */
export default function LinkifiedText({ text, className }) {
    if (text == null || text === "") return null;

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
                            onClick={(e) => e.stopPropagation()}
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
