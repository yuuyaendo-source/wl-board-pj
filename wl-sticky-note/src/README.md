# wl-sticky-note（付箋ボード）— アプリ本体 (src)

Next.js 16、Express、Socket.IO を組み合わせたリアルタイム協調型付箋ボードアプリケーションのソースコードです。

- **プロジェクト名**: `wl-sticky-note`
- **本番サーバ**: `172.16.1.203` / `wlboardsys.internal.wonder-link.com`
- **主要アクセス先**: `/board/wl`

---

## 主な機能

- **付箋操作**: 作成・インライン編集・移動・削除、9色のカラーパレット、ピン留め、グループ化
- **高速ドラッグレンダリング**: `useRef` による直接 DOM 操作により、ドラッグ中の不要な再レンダリングを防止
- **Google Map風パン移動**: Spaceキー＋左ドラッグ、またはマウス中ボタンドラッグでキャンバス全体をスクロール
- **カーソル中心のホイールズーム**: マウスホイールで 0.3x 〜 2.5x の滑らかな拡大・縮小
- **矩形ドラッグ複数選択**: 空き領域ドラッグによる選択ボックス表示、複数付箋の一括選択（Shift追加/解除、Esc全解除）
- **複数付箋の一括移動**: 選択状態の付箋をまとめてドラッグ移動（100ms スロットル同期）
- **グレー付箋トグル切替**: ツールバーの 👁️/🙈 ボタンで完了済み付箋の表示／非表示を切り替え
- **他システム連携 API**: Board System やデスクトップ常駐アプリとの REST API / Socket.IO 通信
- **Board System への直接アクセス**: ツールバー（📋）から統合 4 ボードシステムを開くリンク

---

## 開発環境とローカル起動

### 必要な環境

- Node.js 20.x LTS 以上
- npm 9.x 以上

### セットアップ & 起動

```bash
cd wl-sticky-note/src
npm install
cp .env.example .env
npm run dev
```

ブラウザで [http://localhost:3000](http://localhost:3000) を開いてください。  
代表的なボード例: [http://localhost:3000/board/wl](http://localhost:3000/board/wl)

---

## プロジェクト構造

```
src/
├── app/                    # Next.js App Router
│   ├── page.js             # ボード一覧画面
│   ├── [id]/               # 動的ボード画面（パン移動、ズーム、矩形選択）
│   └── globals.css         # スタイル定義
├── components/             # React コンポーネント
│   ├── StickyNote.js       # 付箋コンポーネント（useRefドラッグ、選択状態、期限表示）
│   ├── Toolbar.js          # ツールバー（ズーム、グレー切替、ボードリンク）
│   ├── CommentListPanel.js # 付箋一覧サイドパネル
│   └── ...
├── server.js               # Express + Socket.IO サーバー（REST API、リアルタイム通信、データ永続化）
├── deploy.sh               # ホストデプロイスクリプト（静的アセットホスト同期対応）
├── ecosystem.config.js     # PM2 設定
├── nginx.conf              # Nginx 設定例
└── package.json
```

---

## 技術スタック

- **フロントエンド**: Next.js 16.x, React 19.x, Three.js (`@pixiv/three-vrm`)
- **バックエンド**: Express.js 5.x, Socket.IO 4.x
- **プロセス管理**: PM2（非 Docker 運用時）/ Docker Compose（本番コンテナ運用時）
- **データストア**: `boards.json`（自動デバウンス保存）

---

## 単体デプロイ・更新コマンド（ホストOS実行時）

```bash
cd /var/www/wlinko-pj/wl-sticky-note/src
npm install
npm run build
# 静的アセットのホスト同期
mkdir -p /var/www/wlinko-pj/shared_static/sticky-note
cp -a .next/static/. /var/www/wlinko-pj/shared_static/sticky-note/
chmod -R a+rX /var/www/wlinko-pj/shared_static/sticky-note/
pm2 restart wl-sticky-note --update-env
```

※ 本番環境で Docker Compose（Blue/Green）を用いる場合は、`board-system/deploy/deploy.sh` により付箋ボードのビルド・起動・バックアップ・静的アセット同期が一括実行されます。
