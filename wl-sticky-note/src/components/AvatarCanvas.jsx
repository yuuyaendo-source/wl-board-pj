'use client';

import React, { useMemo, Suspense, useState, useEffect } from 'react';
import { Canvas, useLoader } from '@react-three/fiber';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { VRMLoaderPlugin } from '@pixiv/three-vrm';
import styles from './AvatarCanvas.module.css';

/**
 * VRM を読み込んで表示する内部コンポーネント
 */
function AvatarModel() {
  const loader = useMemo(() => {
    const gltfLoader = new GLTFLoader();
    gltfLoader.register((parser) => new VRMLoaderPlugin(parser));
    return gltfLoader;
  }, []);

  const gltf = useLoader(loader, '/avatar.vrm');
  const scene = gltf?.userData?.vrm?.scene ?? gltf?.scene;

  if (!scene) return null;

  return <primitive object={scene} />;
}

/**
 * アバター用 Canvas をラップし、画面右下に固定表示するコンポーネント
 * @param {Object} props
 * @param {number} [props.zIndex] - z-index（未指定時は CSS の 50 を使用）
 */
export default function AvatarCanvas({ zIndex }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className={styles.wrapper} style={zIndex != null ? { zIndex } : undefined} aria-hidden>
        <div className={styles.fallback}>アバター読み込み中...</div>
      </div>
    );
  }

  return (
    <div
      className={styles.wrapper}
      style={zIndex != null ? { zIndex } : undefined}
      aria-hidden
    >
      <ErrorBoundary>
        <Suspense fallback={<div className={styles.fallback}>アバター読み込み中...</div>}>
          <Canvas
            camera={{ position: [0.5, 0.3, 1], fov: 45 }}
            gl={{ alpha: true, antialias: true }}
            dpr={[1, 2]}
            style={{ background: 'transparent', width: '100%', height: '100%' }}
          >
            <color attach="background" args={[0, 0, 0, 0]} />
            <ambientLight intensity={0.8} />
            <directionalLight position={[2, 2, 2]} intensity={1.2} />
            <directionalLight position={[-1, 1, 1]} intensity={0.4} />
            <AvatarModel />
          </Canvas>
        </Suspense>
      </ErrorBoundary>
    </div>
  );
}

/**
 * 子の描画エラーを捕捉してメッセージを表示する簡易 Error Boundary
 */
class ErrorBoundary extends React.Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    const message = error?.message ?? String(error);
    return { error: message };
  }

  render() {
    if (this.state.error) {
      return <div className={styles.fallback}>アバターの読み込みに失敗しました</div>;
    }
    return this.props.children;
  }
}
