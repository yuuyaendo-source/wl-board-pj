export interface TextLinkPart {
    type: "text" | "link";
    content: string;
    url?: string;
}

const URL_REGEX = /(https?:\/\/[^\s<>\[\]()]+)/gi;
const MARKDOWN_LINK_REGEX = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/gi;
const URL_DISPLAY_MAX = 40;

export function shortenUrl(url: string): string {
    if (url.length <= URL_DISPLAY_MAX) return url;
    return url.slice(0, URL_DISPLAY_MAX - 1) + "…";
}

/**
 * テキストから URL および Markdown 形式のリンクを抽出し、パーツの配列へ変換する
 */
export function parseTextWithLinks(text?: string | null): TextLinkPart[] {
    if (!text) return [];

    const parts: TextLinkPart[] = [];
    let lastIndex = 0;
    const mdRegex = new RegExp(MARKDOWN_LINK_REGEX.source, "gi");
    let match: RegExpExecArray | null;

    while ((match = mdRegex.exec(text)) !== null) {
        if (match.index > lastIndex) {
            parsePlainTextLinks(text.slice(lastIndex, match.index), parts);
        }
        parts.push({
            type: "link",
            content: match[1],
            url: match[2],
        });
        lastIndex = mdRegex.lastIndex;
    }

    if (lastIndex < text.length) {
        parsePlainTextLinks(text.slice(lastIndex), parts);
    }

    return parts;
}

function parsePlainTextLinks(plainText: string, result: TextLinkPart[]): void {
    let lastIndex = 0;
    const urlRegex = new RegExp(URL_REGEX.source, "gi");
    let match: RegExpExecArray | null;

    while ((match = urlRegex.exec(plainText)) !== null) {
        if (match.index > lastIndex) {
            result.push({
                type: "text",
                content: plainText.slice(lastIndex, match.index),
            });
        }
        result.push({
            type: "link",
            content: shortenUrl(match[0]),
            url: match[0],
        });
        lastIndex = urlRegex.lastIndex;
    }

    if (lastIndex < plainText.length) {
        result.push({
            type: "text",
            content: plainText.slice(lastIndex),
        });
    }
}