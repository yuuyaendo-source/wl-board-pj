"use client";

const URL_REGEX = /(https?:\/\/[^\s<>\[\]()]+)/gi;

/**
 * テキスト中の URL をリンク化して表示する。
 */
export default function LinkifiedText({
  text,
  className,
}: {
  text: string | null | undefined;
  className?: string;
}) {
  if (text == null || text === "") return null;
  const parts: JSX.Element[] = [];
  let lastIndex = 0;
  let keyIndex = 0;
  let m;
  const re = new RegExp(URL_REGEX.source, "gi");
  while ((m = re.exec(text)) !== null) {
    if (m.index > lastIndex) {
      parts.push(<span key={`t-${keyIndex++}`}>{text.slice(lastIndex, m.index)}</span>);
    }
    const url = m[0];
    parts.push(
      <a
        key={`a-${keyIndex++}`}
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-600 underline hover:text-blue-800"
        onClick={(e) => e.stopPropagation()}
      >
        {url}
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
