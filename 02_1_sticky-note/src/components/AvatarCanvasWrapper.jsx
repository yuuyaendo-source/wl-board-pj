'use client';

import dynamic from 'next/dynamic';

// 読み込み中は右下にプレースホルダを表示（アバター領域を確保）
function AvatarLoadingPlaceholder() {
  return (
    <div
      style={{
        position: 'fixed',
        bottom: 0,
        right: 0,
        width: 280,
        height: 360,
        minWidth: 280,
        minHeight: 360,
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 12,
        color: '#666',
        background: 'rgba(255,255,255,0.9)',
      }}
      aria-hidden
    >
      アバター読み込み中...
    </div>
  );
}

// Three.js はクライアントのみで実行するため dynamic import（ssr: false）
const AvatarCanvas = dynamic(
  () => import('@/components/AvatarCanvas').then((mod) => mod.default),
  { ssr: false, loading: AvatarLoadingPlaceholder }
);

export default function AvatarCanvasWrapper() {
  return <AvatarCanvas />;
}
