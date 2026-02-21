# AI-Board・Desktopアプリの開発の進め方

wl-sticky-note（本番: http://wl-sticky-note.local/board/wl）と連携する **AI-Board** と **Desktopアプリ** の開発・配布の進め方を整理したドキュメントです。

---

## 1. 方針の整理

| アプリ | 開発の進め方 | ゴール |
|--------|--------------|--------|
| **Desktopアプリ** | 本番の sticky-note への連携が確認できたら、**一旦メンバーにアプリとして配布**する。 | メンバーがトレイで付箋お知らせ・パーソナルモードを利用できるようにする。 |
| **AI-Board** | **本番の sticky-note との連携を確認しながら**開発を進める。 | 本番の付箋ボード（board: wl）に付箋を送信・AIコメント連携ができるようにする。 |

---

## 2. Desktopアプリの進め方

### 2.1 本番 sticky-note 連携の確認

本番の付箋ボード（http://wl-sticky-note.local/board/wl）と連携できることを確認してから配布する。

1. **設定を本番向けにする**
   - `config.json` の `postit_board_url`: `http://wl-sticky-note.local/`
   - `postit_board_id`: `wl`
   - （任意）`ai_board_url` を本番の AI-Board URL に変更

2. **動作確認**
   - Desktopアプリを起動（`.\start_app.ps1` など）
   - トレイの「アイコンクリックで開く」で **http://wl-sticky-note.local/board/wl** が開くこと
   - 本番の付箋ボードに新付箋を追加し、一定時間後に「新しい付箋が投稿されました」トーストが出ること（ポーリング連携）
   - トーストをクリックして該当ボードが開くこと

3. **問題なければ「本番連携OK」として配布準備へ**

### 2.2 メンバーへの配布

**配布物**: **MSI**（推奨）または 02_3_WL_Desktop_app フォルダ（ZIP）

**前提**: メンバーのPCは **本番の付箋ボード（wl-sticky-note.local）にネットワークからアクセスできる**こと。**会社ポリシーで exe 直接実行が不可**なため、**MSI 形式**またはフォルダ＋起動手順で配布する。

**MSI 形式で配布（推奨）**

1. 開発側: 本番向けの `config.json`（`postit_board_url`: `http://wl-sticky-note.local/`、`postit_board_id`: `wl`）を 02_3_WL_Desktop_app に置く。
2. `cd 02_3_WL_Desktop_app` のうえで `.\build_msi.ps1` を実行。`dist\WonderRinko.msi` が生成される。
3. **WonderRinko.msi** を配布。メンバーは MSI を実行してインストール（Python 不要）。インストール後、トレイにアイコンが出ればOK。必要に応じてインストール先の `config.json` で `user_id` を変更。

**フォルダ＋起動手順で配布**

1. 02_3_WL_Desktop_app を ZIP などで配布（`.venv` は含めずにOK）
2. メンバーに依頼する内容:
   - Python 3.10 以上をインストール
   - 解凍したフォルダで `.\start_app.ps1` を実行（初回は venv 作成・pip install が走る）
   - トレイにアイコンが出ればOK。必要に応じて `config.json` の `user_id` を変更
3. 本番向けの初期設定として、`config.json` に以下を入れた状態で配布するとよい:
   - `postit_board_url`: `http://wl-sticky-note.local/`
   - `postit_board_id`: `wl`

### 2.3 開発時の注意

- **ローカル開発**: `postit_board_url` を `http://127.0.0.1:3000/` にし、ローカルの wl-sticky-note で確認
- **配布用**: 上記のとおり本番 URL・board_id `wl` を入れた状態でパッケージ化する

---

## 3. AI-Board の進め方

### 3.1 本番 sticky-note との連携を確認しながら開発

本番の付箋ボード（http://wl-sticky-note.local/board/wl）に付箋を送り、AIコメント連携まで確認できるようにする。

1. **本番向けの設定**
   - `src/config.json` の `board_id`: `wl`
   - 環境変数 **`POSTIT_BOARD_URL=http://wl-sticky-note.local`** を設定（.env またはシステム環境変数）
   - これで付箋検知・Webアプリからの送信先が本番の sticky-note になる

2. **連携確認の手順**
   - 本番の付箋ボードをブラウザで開く: http://wl-sticky-note.local/board/wl
   - AI-Board（Flask）と付箋検知（sticky_note_detector.py）を、上記設定で起動
   - 付箋検知で検出した付箋が本番ボード「wl」に追加されること、AI-Board 経由でコメントが返ることなどを確認

3. **開発の進め方**
   - 機能追加・修正はローカルで行い、**本番の sticky-note（wl）向けに送信できる状態**で都度確認する
   - 本番サーバ（wl-sticky-note.local）にネットワークからアクセスできる開発環境であれば、`POSTIT_BOARD_URL=http://wl-sticky-note.local` のまま開発・検証できる
   - 本番にアクセスできない環境では、一度ローカルで sticky-note（localhost:3000）と連携確認し、本番デプロイ後に本番 URL で再確認する

### 3.2 環境切り替えの整理

| 確認したい相手 | board_id | POSTIT_BOARD_URL |
|----------------|----------|------------------|
| ローカルの sticky-note | wl（または開発用ID） | 未設定 or http://localhost:3000 |
| 本番の sticky-note | wl | http://wl-sticky-note.local |

---

## 4. 共通：本番連携の確認チェックリスト

- [ ] **付箋ボード本番**が http://wl-sticky-note.local/board/wl で開ける
- [ ] **Desktopアプリ**: `postit_board_url` 本番、`postit_board_id`: wl で、トレイからボードが開ける／新付箋でトーストが出る
- [ ] **AI-Board**: `POSTIT_BOARD_URL=http://wl-sticky-note.local`、`board_id`: wl で、本番ボードに付箋が送られる／AIコメントが連携する

---

## 5. まとめ

- **Desktopアプリ**: 本番 sticky-note 連携を確認 → 問題なければ **MSI 形式**（推奨）または **フォルダ＋起動手順**でメンバーに配布する（会社ポリシーにより exe 単体配布は行わず、MSI または Python 起動とする）。
- **AI-Board**: **本番の sticky-note（board: wl）への送信・連携を確認しながら**開発。`POSTIT_BOARD_URL` と `board_id` で本番向けに切り替えて検証する。

関連: wl-sticky-note 本体の開発フローは **`docs/開発の進め方.md`** を参照してください。
