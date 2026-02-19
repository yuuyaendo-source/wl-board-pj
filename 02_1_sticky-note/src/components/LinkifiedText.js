"use client";

/**
 * テキスト中の URL（http/https）を <a> タグでリンク化して表示する。
 * 長い URL は省略表示（ホバーで全文表示）。
 */
const URL_REGEX = /(https?:\/\/[^\s<>\[\]()]+)/gi;
const URL_DISPLAY_MAX = 40;

function shortenUrl(url) {
    if (url.length <= URL_DISPLAY_MAX) return url;
    return url.slice(0, URL_DISPLAY_MAX - 1) + "…";
}

export default function LinkifiedText({ text, className }) {
    if (text == null || text === "") return null;
    const parts = [];
    let lastIndex = 0;
    let keyIdx = 0;
    let m;
    const re = new RegExp(URL_REGEX.source, "gi");
    while ((m = re.exec(text)) !== null) {
        if (m.index > lastIndex) {
            parts.push(<span key={`t-${keyIdx++}`}>{text.slice(lastIndex, m.index)}</span>);
        }
        const url = m[0];
        const display = shortenUrl(url);
        parts.push(
            <a key={`a-${keyIdx++}`} href={url} target="_blank" rel="noopener noreferrer" title={url} onClick={(e) => e.stopPropagation()}>
                {display}
            </a>
        );
        lastIndex = re.lastIndex;
    }
    if (lastIndex < text.length) {
        parts.push(<span key={`t-${keyIdx++}`}>{text.slice(lastIndex)}</span>);
    }
    return <span className={className}>{parts.length ? parts : text}</span>;
}
