# wlinko-pj (Wonder Link Project)

浅川研究室のプロジェクト群です。AI、Web技術、そしてアバターインタラクションを組み合わせた実験的なアプリケーションを含みます。

## 📁 プロジェクト構成

| ディレクトリ / ファイル | 説明 |
|------------------------|------|
| **02_1_App_postit_board** | 付箋掲示用Webアプリ（Next.js + Express + Socket.IO）。ポート3000で動作。 |
| **02_2_AI-Board** | **[メイン開発中]** AI搭載デジタルボード（Flask + Socket.IO）。ポート5000で動作。 |
| **docs** | 共通ドキュメント・仕様書 |
| **start_all_servers.ps1** | 両サーバーを一括起動するPowerShellスクリプト（推奨） |

---

# 🤖 02_2_AI-Board

物理的な付箋とデジタルアバターが融合した、インタラクティブな掲示板システムです。
カメラで検出した付箋に対して、AIキャラクター（Wonder Link-ko / リン子）がリアクションし、コメントを読み上げます。

## ✨ 主な機能

1.  **リアルタイム付箋同期**
    *   Webカメラで付箋を検出し、デジタルボード上にリアルタイム反映。
    *   `StickyNoteDetector` (OpenCV) による画像認識。
2.  **AIインタラクション**
    *   **画像認識 & テキスト生成**: Google Gemini API を使用して付箋の内容を理解し、コメントを生成。
    *   **音声合成**: VOICEVOX を使用してコメントを読み上げ。感情タグ（例: `[Anger]`）は自動除去され、自然な発話が可能。
    *   **感情表現**: AIが `[JOY]`, `[ANGRY]` などの感情タグを出力し、アバターの表情や声に反映。
3.  **3Dアバター (VRM)**
    *   Webブラウザ上で動作する3Dキャラクター (`@pixiv/three-vrm`, `Three.js`)。
    *   **リップシンク**: ブラウザの `AudioContext` を用いて、音声波形に合わせて口パクを自動生成。
    *   **自律動作 (Autonomous)**: 呼吸、ランダムな視線移動、発話時の手振りなどを自動で行い、生き生きとした存在感を表現。
    *   **フルコントロール**: 位置 (X/Y/Z)、回転 (Rot Y)、スケール、表示枠 (Window Scale/Pos) をGUIで自由に変更可能。
    *   **モード切替**: AI-Boardモード (自律)、Receptionモード (開発中)、Personalモード (開発中) の基盤を実装済み。

## 🛠 技術スタック

### Backend (Python)
*   **Framework**: Flask, Flask-SocketIO
*   **AI/ML**: Google Generative AI (Gemini), OpenCV (CV2), NumPy
*   **Audio**: VOICEVOX (HTTP API経由)

### Frontend (Web)
*   **Core**: HTML5, CSS3, JavaScript (ES Modules)
*   **3D/Avatar**: Three.js (r170), @pixiv/three-vrm (v3)
*   **Real-time**: Socket.IO Client

## 🚀 セットアップ & 起動

### 必要要件
*   Python 3.10+
*   Node.js (for 02_1_App_postit_board)
*   VOICEVOX (別途起動が必要な場合あり、現状はHTTP API利用)
*   Google Gemini API Key (`.env` に記載)

### 起動方法
ルートディレクトリ (`wlinko-pj`) で以下のスクリプトを実行してください。

```powershell
.\start_all_servers.ps1
```

これにより、以下の2つのサーバーが起動します。
1.  **Web App**: `http://localhost:3000`
2.  **AI-Board**: `http://localhost:5000` (アバターはこちらで動作)

## 🎮 アバター操作 (AI-Board)

`http://localhost:5000` にアクセス後、画面左下の **Avatar Settings** をクリックすると設定パネルが開きます。

*   **Visible**: 表示/非表示
*   **Scale**: アバターの拡大縮小
*   **Pos X / Y / Z**: アバターの3次元位置調整
*   **Rot Y**: アバターのY軸回転
*   **Win Scale**: 表示ウィンドウ全体のサイズ変更
*   **Win X / Y**: 表示ウィンドウの画面内位置変更

## 📝 現在の開発状況 (2026/01/31時点)

*   ✅ **Phase 1: 基本機能** (完了)
    *   付箋検出～AI回答～音声再生～リップシンクの一連フロー
    *   アバター表示・操作UI (位置・回転・サイズ・枠) の完全実装
    *   **自律動作強化**: ランダムな視線、呼吸、発話ジェスチャーの実装
    *   **品質改善**: 感情タグ読み上げ防止、アバターポーズの自然化
*   🚧 **Phase 2: モード拡張** (計画中)
    *   受付モード (Webカメラによるフェイストラッキング・Vtuber化)
    *   パーソナルモード (顔認識によるユーザー特定)
