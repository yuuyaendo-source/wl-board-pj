"use client";

/**
 * テキスト中の URL（http/https）を <a> タグでリンク化して表示する。
 * テキスト部分は React のデフォルトでエスケープされる。
 */
const URL_REGEX = /(https?:\/\/[^\s<>\[\]()]+)/gi;

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
        parts.push(
            <a key={`a-${keyIdx++}`} href={url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                {url}
            </a>
        );
        lastIndex = re.lastIndex;
    }
    if (lastIndex < text.length) {
        parts.push(<span key={`t-${keyIdx++}`}>{text.slice(lastIndex)}</span>);
    }
    return <span className={className}>{parts.length ? parts : text}</span>;
}
