# Wonder Linko Desktop App (DT_APP)

社員PCに常駐する「Personal Linko Agent」。タスクトレイ常駐＋**ミニポート**（付箋クイック投稿）を起動時に表示し、各自の **Board System パーソナルボード**へワンクリックで誘導する。**来客通知**・**リン子アバター**・**ブレストチャット**などの機能は、設定でユーザーが任意に ON にする（既定はすべて OFF）。

> バージョンは `version.py`（`__version__`）で一元管理。MSI/exe ビルドと更新チェックはこの値を参照する。

## 開発環境と利用環境

- **開発環境** … **Linux** を想定。`pip install -r requirements.txt` は Linux でそのまま実行可能（Windows 専用のトースト用パッケージは自動でスキップされる）。**MSI ビルドは Windows で行う**（Linux で `./build_msi.sh` を実行すると案内メッセージが出る）。
- **利用環境（配布先）** … **Windows** が前提（トースト通知・MSI 配布・スタートアップ登録・音声再生は Windows のみ）。Mac では一部機能（トレイ・ミニポート・ボタン類）が動くが、トースト・音声・スタートアップ登録は無効。**iPhone** ではデスクトップアプリは使わず、Board System のパーソナルボード等をブラウザ（Safari 等）で開く。

## 機能

### 常時動作（既定 ON）

- **ミニポート（付箋クイック投稿）** … 起動時に**画面上にミニポートを強制表示**。リン子ボタン・「投稿」で付箋を素早く投稿できる。✕ ボタン・右クリックで非表示にでき、トレイ「ミニポートを表示」で再表示可能。
- **タスクトレイ常駐** … アプリ本体はタスクトレイに常駐。左クリックで設定した先（既定: 付箋ボード）を開く。右クリックメニューは最小限（開く・設定・ミニポート表示・終了）。
- **アイコンクリックで開く先の切替** … 設定画面「トレイアイコン左クリックで開く先」で、付箋ボード／パーソナル／最後のお知らせを切替可能（`tray_click_action`）。
- **「ボード」ボタン（ミニポート）** … ミニポートの「ボード」で**各自の Board System パーソナルボード**を開く。初回はメールアドレスを入力すると Board System の `/users/by_email` でユーザーが解決され、`board_system_personal_id`・`user_id`・`display_name` が保存される（以降は同じ PC でそのまま開く）。
- **付箋ボード連携（ポーリング）** … 付箋ボード（`postit_board_id` / `postit_board_ids`）を `postit_poll_interval_sec`（既定 60 秒、0 で無効）でポーリングし、新付箋が増えたら「新しい付箋が投稿されました」とトースト。「最後のお知らせを開く」で該当ボードを開ける。
- **右下トーストお知らせ** … 業務の邪魔にならない位置に通知。**表示中にクリック**するとそのお知らせの URL へ飛べる。トーストの**アイコン**は `toast_icon_path` で変更可能（未設定時は `assets/` のアイコン）。**Windows の設定で通知をオフにすると、アプリ・再インストールではオンに戻せません。** トレイの「通知を表示」はアプリ内のオン/オフ（Windows の設定とは別）。詳細は `docs/Windows通知がオフになった場合.md`。
- **表示名（付箋の投稿者名）** … 起動時に未設定なら入力を促す。トレイ「表示名を変更（付箋の投稿者名）」や設定ダイアログで変更可能（`display_name`）。
- **PC起動時に自動で起動** … **MSI 版の初回起動時**にスタートアップへ自動登録（レジストリ）。トレイ「PC起動時に自動で起動」で ON/OFF。
- **自動更新（任意）** … `update_check_url` を設定すると起動時にバックグラウンドで更新チェック（ダイアログは出さずログのみ）。トレイ「アプリをアップデート」や設定ダイアログの「アップデート確認」で手動チェック・インストール。
- **設定ダイアログ** … トレイ「設定...」やミニポートの「設定」から開く。表示名と**機能フラグ（features）**の ON/OFF を 1 画面で切替。

### 任意機能（features.* 既定 OFF・設定ダイアログで ON）

| feature キー | 内容 |
|--------------|------|
| `taskbar_mode` | フローティングのミニポートではなく、通常 Window としてタスクバーに常駐する |
| `linko_avatar` | ミニポートにリン子の **2D アバター**（11 ポーズ・表情切替・口パク・アイドルアニメ）を表示。`assets/avatar/` の画像を読み込む |
| `visitor_notify` | 受付（linko-system）の `visitor_arrived` を Socket.IO で受信し、**来客をトースト通知**。クリックで remote_unlock パネル等を開く |
| `visitor_notify_sound` | `visitor_notify` が ON のとき、受付で再生されたものと同じ**音声をデスクトップでも再生**（会議中は OFF 推奨。Windows のみ） |
| `brainstorm` | アバタークリックで**リン子とのブレストチャット**を開く。Board System の `/brainstorm`（SSE ストリーミング）に会話履歴を送り、応答を 1 トークンずつ表示。**PDF/Word/テキストの添付**（端末内でテキスト抽出し社内 LLM にのみ渡す）、リン子の回答を**付箋ボードへ投稿**するボタン付き |

> アバター・音声・ブレストは **CATO 経由で社内 LAN（linko-system / Board System）に到達できること**が前提。

## トレイメニュー構成

ミニポートの ⚙ 設定・🔕 通知・右クリックメニューで大半の操作が可能なため、トレイ右クリックは次のみ。

- **開く**（左クリックと同じ。開く先は設定画面で変更）
- **設定...**
- **ミニポートを表示**（非表示にしたあと再表示する用）
- **終了**

通知 ON/OFF・アップデート確認・表示名・機能 ON/OFF・起動時自動起動などは **ミニポートの設定画面** から操作する。

## 必要な環境

- **開発時** … Linux または Windows。Python 3.10+。Linux では `pip install -r requirements.txt` で Windows 専用パッケージ（pywin32 / winotify / win10toast 系）はスキップされる。
- **利用時** … Windows 10/11（推奨）。トースト通知・音声再生・スタートアップ登録は **Windows のみ**。
- **主な依存**（`requirements.txt`） … pystray, Pillow, requests, customtkinter, pynput, python-socketio[client]（来客通知）, pypdf / python-docx（ブレストの資料添付）。

## セットアップ・起動

**Linux（開発環境）:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

**Windows（開発または利用）:**

```powershell
cd wl_desktop_app
.\start_app.ps1
```

または:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## 配布について

**exe ファイル単体の配布・実行は多くの社内環境で許可されない**ことがあります。そのため配布は **MSI 形式を推奨**します。

- **MSI 形式（推奨）** … Windows インストーラー（.msi）で配布。`.\build_msi.ps1` でビルド。**exe が許可されない環境では必ず MSI を使用してください。**
- **単体 exe** … `.\build_exe.ps1` で `dist\WonderRinko.exe` を生成。exe の実行が許可されている環境のみで利用。
- **フォルダ＋起動手順** … 本フォルダを ZIP で配布し、メンバーに Python 3.10+ と `.\start_app.ps1` での起動を依頼する。

## MSI ビルド（配布用）

**MSI は Windows 上でビルドしてください。** Linux で `./build_msi.sh` を実行すると「Windows で PowerShell を実行してください」と案内されます。

**Windows で PowerShell を開き:**

```powershell
cd wl_desktop_app
.\build_msi.ps1
```

- 要: Python 3.10+。`build_msi.ps1` が `requirements.txt` と cx_Freeze / freeze-core を自動インストールし、`build/` `dist/` をクリーンしてからビルドする。
- ビルド後に **PIL（`_imaging*.pyd`）と python-socketio / engineio のバンドル漏れを自動チェック**（漏れていれば配布せずエラー終了）。
- 出力: `dist\WonderLinko.msi`（`setup.py` の `output_name` / `target_name=WonderLinko.exe`）。
- インストール先: per-user の `C:\Users\<user>\AppData\Local\WonderLink\WonderLinko`（管理者不要）。
- インストール後、デスクトップの「Wonder Linko」を起動するとタスクトレイに常駐し、**ミニポートが画面上に表示**される。初回起動時に「PC起動時に自動で起動」が自動で ON になる。

> ⚠️ **config.json は MSI にバンドルしません**（v3.1.4 以降）。上書きインストールで既存ユーザーの設定（`features.*` 等）がリセットされる事故を防ぐためです。**新規インストール時は `config_loader.py` の defaults（＝本番 URL）でそのまま動作**します。本番 URL を変えたい場合は defaults を編集してビルドするか、各端末に `config.json` を配置してください。

## 設定（config.json）

`config.json` が無くても `config_loader.py` の defaults（本番 URL）で動作します。主なキー:

| キー | 説明 |
|------|------|
| `user_id` | 利用者 ID（メールログインで Board System の user id に更新される。未設定時は `WLINKO_USER_ID` / `USERNAME`） |
| `display_name` | 付箋の投稿者名（起動時に入力を促す） |
| `board_system_url` | Board System の API ベース URL（例: `https://wl-ai-board.internal.wonder-link.com/api/bs`）。パーソナル・ブレストで使用 |
| `board_system_personal_id` | メールログインで取得した user id。設定時は「パーソナルを開く」で Board System のパーソナルボードを開く |
| `postit_board_id` / `postit_board_ids` | トレイクリックで開く既定ボード（本番: `wl`）／ 新付箋を監視するボード ID の配列 |
| `postit_poll_interval_sec` | 付箋ポーリング間隔（既定 60 秒、0 で無効） |
| `tray_click_action` | トレイクリックで開く先: `postit` / `personal` / `last_notification` |
| `mini_port_api_url` | ミニポートの付箋投稿先（**ブラウザで開く付箋ボードと同一ホスト・ポートである必要あり**） |
| `mini_port_taskboard_url` | リン子クリックで開く Task ボード URL |
| `linko_server_url` | linko-system（受付サーバ）の URL。`features.visitor_notify` で接続して来客通知を受ける |
| `ai_board_url` / `postit_board_url` | レガシー AI ボード URL（パーソナルのフォールバック等） |
| `toast_icon_path` / `toast_duration_sec` / `notifications_enabled` | トーストのアイコン・表示秒数・アプリ内オン/オフ |
| `update_check_url` | 更新チェック用 JSON の URL（`.json`・HTTPS 必須） |
| `update_network_check_host` / `..._interval_sec` / `..._max_wait_sec` | 起動時更新チェック前に Ping でネットワーク確立を待つ先・間隔・最大待機 |
| `features` | 任意機能フラグ（`taskbar_mode` / `linko_avatar` / `visitor_notify` / `visitor_notify_sound` / `brainstorm`） |
| `security` | 外向き URL の許可設定（下記） |

- 環境変数で上書き可能: `WLINKO_USER_ID`, `AI_BOARD_URL`, `POSTIT_BOARD_URL`, `MINI_PORT_API_URL`, `MINI_PORT_TASKBOARD_URL`, `BOARD_SYSTEM_URL`, `LINKO_SERVER_URL`（`.env` またはシステム環境変数）。
- 本番用テンプレートは `config.production.example.json`。これを `config.json` にコピーして URL を環境に合わせてから配布/ビルドできる。

### セキュリティ（外向き URL の許可リスト・`security.py`）

config.json の改ざんや Socket.IO 由来の `click_url` で社外へ誘導されないよう、HTTP(S) 先をホワイトリストで制限します。

- 既定で許可: `*.internal.wonder-link.com` サフィックスと `localhost` / `127.0.0.1`。
- `config.json` の `security.allowed_host_suffixes` / `security.allowed_hosts` / `security.allow_private_ips` で調整。
- 開発で LAN IP を使う場合（環境変数）: `WLINKO_EXTRA_ALLOWED_HOSTS=172.16.1.251`、`WLINKO_ALLOW_PRIVATE_IPS=1`。
- 緊急時のみ許可リスト無効化: `WLINKO_DISABLE_URL_ALLOWLIST=1`。
- `update_check_url` は HTTPS かつ `.json`、MSI ダウンロードは HTTPS かつ `.msi` を要求。`board_system_personal_id` は path インジェクション防止のため `[A-Za-z0-9_-]` のみ許可。

## 自動更新（update_check_url）

`config.json` の **`update_check_url`** に最新版情報の JSON を返す URL を設定すると次の動作をします。

- **起動時**: バックグラウンドでチェックし、新しいバージョンがあっても**ダイアログは出さずログに残すだけ**（更新は任意・手動）。`update_network_check_host` 設定時は Ping でネットワーク確立を待ってからチェック。
- **トレイ「アプリをアップデート」/ 設定の「アップデート確認」**: チェックし、最新なら「最新版です」、更新があれば確認の上 MSI をダウンロードしてインストール。完了後にアプリが自動で再起動する。

**サーバー側で用意する JSON**:

```json
{
  "version": "1.0.1",
  "url": "https://example.com/wonderlinko/WonderLinko.msi"
}
```

- `version`: 最新のバージョン番号（現在のアプリより新しければ更新ありとみなす）。
- `url`: そのバージョンの MSI の **HTTPS ダウンロード URL**（`.msi`）。

**Board System 内で配布する場合**（推奨）: 同じリポジトリの `board-system/backend/desktop_app_releases/` に MSI と `latest.json` を配置すると、Board System の API から配信される。

- 更新チェック用 URL: `https://<Board System のドメイン>/api/bs/desktop-app/latest.json`
- 例（本番）: `https://wl-ai-board.internal.wonder-link.com/api/bs/desktop-app/latest.json`

⚠️ **重要**: backend Dockerfile が `desktop_app_releases/` をビルド時 COPY しているため、**ホスト側のファイルを差し替えただけでは反映されません**。新バージョンリリース時は `board-system/deploy/deploy.sh` で backend を blue/green 再ビルドする必要があります。詳細:

- `docs/v3_リリース手順.md` — 完全なリリース手順 + トラブルシューティング
- `board-system/backend/desktop_app_releases/README.md` — アップロード手順

## ユーザー管理・Board System との共通化

- **ユーザーデータベース** … パーソナル・ブレストで使うユーザーは Board System の API（`/users/by_email` など）で解決する。Board System と Linko は同一の PostgreSQL の `users` テーブルを参照するため、**ユーザーは共通**。
- **ユーザー登録** … 新規ユーザーは Board System 側で登録する（管理画面または `POST /users`）。登録済みメールアドレスをデスクトップアプリの初回メール入力で入れると、そのユーザーに紐づきパーソナルボードが開く。

## ドキュメント

- `docs/v3_リリース手順.md` — MSI ビルド〜配信のリリース手順
- `docs/v2_拡張計画.md` — features.* の拡張計画
- `docs/MSI起動エラー_デバイス側の確認.md` — MSI 版が起動しないときのデバイス側チェック
- `docs/Windows通知がオフになった場合.md` — 通知が出ないときの対処（`通知設定をリセットする.ps1` 同梱）

## 今後の拡張（開発プラン）

- ブレストのリン子発言からの付箋投稿の高度化、音声入力との連携
- アバターの演出強化・自律動作
- 適切なタイミングでのニュース・付箋投稿の促し
