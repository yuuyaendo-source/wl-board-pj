# Wonder Rinko Desktop App (DT_APP)

社員PCに常駐する「Personal Rinko Agent」。**各ユーザー用のパーソナルモード**（`/personal?user=xxx`）へワンクリックで誘導し、お知らせからのDeep Linkを提供する。

## 開発環境と利用環境

- **開発環境** … **Linux** を想定。`pip install -r requirements.txt` は Linux でそのまま実行可能（Windows 専用のトースト用パッケージは自動でスキップされる）。**MSI ビルドは Windows で行う**（Linux で `./build_msi.sh` を実行すると案内メッセージが出る）。
- **利用環境（配布先）** … **Windows** または **Mac**（デスクトップアプリ）。トースト通知・MSI 配布・スタートアップ登録は **Windows のみ**。**iPhone** ではデスクトップアプリは利用せず、Board System のパーソナルボード等はブラウザ（Safari 等）でアクセスする。

## 機能

- **ミニポート（付箋クイック投稿）** … 起動時に**画面上にミニポートを強制表示**。リン子ボタン・「投稿」で付箋を素早く投稿できる。トレイメニュー「ミニポート」「ミニポートを表示」「ミニポートを非表示」で任意に表示/非表示を切り替え可能。
- **Windows MSI でインストール** … MSI でインストール後、デスクトップのショートカットから起動。起動するとタスクトレイに常駐し、ミニポートが画面上に表示される。
- **タスクトレイ常駐** … アプリ本体はタスクトレイに常駐。トレイからミニポートの表示/非表示や各種メニューにアクセス。
- **パーソナルモードを開く** … トレイの「パーソナルモードを開く」で、**このユーザー用**のパーソナル画面をブラウザで開く。`board_system_url` とメールログイン済みの場合は Board System のパーソナルボード（`/boards/personal/{id}`）、そうでなければ AIボードの `/personal?user=ユーザーID`。起動時に自動で開く動作は行わない。
- **「ボード」ボタン（ミニポート）** … ミニポートの「ボード」をクリックすると**各自の Board System パーソナルボード**を開く。初回のみメールアドレスを入力すると、Board System のユーザーと紐づき `board_system_personal_id` が保存され、以降は同じ PC でそのままパーソナルが開く。`board_system_url` が未設定の場合はタスクボードを開く。
- **アイコンクリックで開く** … トレイアイコンをクリックすると設定した先（デフォルト: 付箋ボード）を開く。メニュー「アイコンクリックで開く」で付箋ボード／パーソナル／最後のお知らせを切り替え可能。
- **PC起動時に自動で起動** … **初回起動時**にスタートアップへ自動登録し、**Windows 再起動後もミニポートが自動で表示**される。メニュー「PC起動時に自動で起動」でON/OFFを切り替え可能（レジストリのスタートアップに登録）。
- **付箋ボード連携** … 付箋ボード（`postit_board_id`）を一定間隔でポーリングし、新付箋が増えたら「新しい付箋が投稿されました」とトースト。「最後のお知らせを開く」で該当ボードを開ける。
- **右下トーストお知らせ** … 業務の邪魔にならない位置に通知。**表示中にクリック**するとそのお知らせのURLへ飛べる。トレイの「最後のお知らせを開く」でも開ける。トーストの**アイコン**は `toast_icon_path` で変更可能（未設定時はトレイと同じ緑の丸デザイン）。**Windows の設定で通知をオフにすると、アプリ・再インストールではオンに戻せません。** トレイメニュー「通知が表示されない場合」で手順を表示。詳細は `docs/Windows通知がオフになった場合.md`。
- **アバター表示/非表示** … メニューでトグル（設定のみ保存。アバター表示は今後実装）。
- **音声ON/OFF** … メニューでトグル。

## 必要な環境

- **開発時** … Linux または Windows。Python 3.10+。Linux では `pip install -r requirements.txt` で Windows 専用パッケージはスキップされる。
- **利用時（デスクトップアプリ）** … Windows 10/11 または Mac。トースト通知は **Windows のみ**（win10toast / pywin32）。Mac ではトレイ・ミニポート・「ボード」ボタン等は利用可能で、トーストは表示されない。

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
cd 02_3_WL_Desktop_app
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

- **MSI 形式（推奨）** … Windows インストーラー（.msi）で配布。多くの企業ポリシーで許可され、インストール・アンインストールが標準で管理できる。`.\build_msi.ps1` でビルド。**exe が許可されない環境では必ず MSI を使用してください。**
- **単体 exe** … `.\build_exe.ps1` で `dist\WonderRinko.exe` を生成可能。exe の実行が許可されている環境のみで利用。
- **フォルダ＋起動手順** … 本フォルダを ZIP で配布し、メンバーに Python 3.10+ と `.\start_app.ps1` での起動を依頼する。

## MSI ビルド（配布用）

**MSI は Windows 上でビルドしてください。** Linux で `./build_msi.sh` を実行すると「Windows で PowerShell を実行してください」と案内されます。

**Windows で PowerShell を開き:**

```powershell
cd 02_3_WL_Desktop_app
.\build_msi.ps1
```

- 要: Python 3.10+（cx_Freeze を自動インストール）
- 出力: `dist\WonderLinko.msi`（setup.py の target_name による）
- 配布: MSI を渡し、メンバーはダブルクリックでインストール。インストール後、デスクトップの「Wonder Linko」を起動するとタスクトレイに常駐し、**ミニポートが画面上に表示**される。初回起動時に「PC起動時に自動で起動」が自動でONになり、**Windows 再起動後もミニポートが自動表示**される。インストール先の `config.json` はビルド時に同梱したものが使われるため、**ビルド前に本番用の config.json を置いておく**とよい。

## 設定

- `config.json` … `user_id`、`personal_path`、**`board_system_url`**（Board System の API ベース URL。例: 本番 `https://wl-ai-board.internal.wonder-link.co.jp/api/bs`。設定すると「ボード」クリック・パーソナルで Board System のパーソナルボードを開ける）、**`board_system_personal_id`**（メールログインで設定される user id。空のときは初回にメール入力）、**`postit_board_id`**（トレイクリックで開くデフォルトボード。本番: `wl`）、**`postit_board_ids`**（新付箋を監視するボードIDの配列。未設定時は `postit_board_id` のみ）、`postit_poll_interval_sec`、**`tray_click_action`**、**`toast_icon_path`**、AIボードURL・付箋ボードURL、アバター・音声のON/OFFなど
- 環境変数 `WLINKO_USER_ID` でユーザーIDを指定可能。`AI_BOARD_URL`, `POSTIT_BOARD_URL` でURLを上書き可能（`.env` やシステム環境変数）
- **ミニポートの送信先** … `mini_port_api_url`（例: `https://wl-ai-board.internal.wonder-link.co.jp/board/wl`）から POST 先を導出。**ここで指定したホスト・ポートは、ブラウザで開いている付箋ボードの URL と同一である必要があります。** 別のサーバーを指していると送信は成功しても表示されません。表示されない場合は付箋ボードのページを再読み込み（F5）してみてください。
- **自動更新** … `update_check_url` に JSON の URL を設定すると、起動時に更新チェックし、トレイメニュー「更新を確認」で手動チェック・インストールが可能。未設定時は更新チェックを行わない。

## 自動更新（update_check_url）

`config.json` の **`update_check_url`** に、最新版情報の JSON を返す URL を設定すると次の動作をします。

- **起動時**: バックグラウンドでその URL に GET し、現在より新しいバージョンがあればトーストで「新しいバージョン X が利用可能です。トレイの『更新を確認』からインストールできます。」と通知する。
- **トレイメニュー「更新を確認」**: 同じ URL でチェックし、最新版なら「最新版です」、更新があれば「今すぐダウンロードしてインストールしますか？」と確認し、Yes で MSI をダウンロードしてインストーラーを起動する。

**サーバー側で用意する JSON**（例: `https://example.com/wonderlinko/latest.json`）:

```json
{
  "version": "1.0.1",
  "url": "https://example.com/wonderlinko/WonderLinko.msi"
}
```

- `version`: 最新のバージョン番号（例: 1.0.1）。現在のアプリより新しければ更新ありとみなす。
- `url`: そのバージョンの MSI のダウンロード URL。

配布用 MSI とこの JSON を同一オリジンまたは CORS 許可された場所に置き、本番の `config.json` に `update_check_url` を設定してビルドすると、ユーザーはトレイからワンクリックで更新できる。

## 配布方法

- **MSI（推奨）** … `.\build_msi.ps1` で `dist\WonderLinko.msi` を生成し配布。メンバーはインストーラーでインストール（Python 不要）。**exe が許可されない環境ではこちらを使用すること。**
- **単体 exe** … `.\build_exe.ps1` で `dist\WonderRinko.exe` を生成。exe 実行が許可されている場合のみ。
- **フォルダ＋起動手順** … 本フォルダを ZIP で配布。メンバーは Python 3.10+ を入れ、`.\start_app.ps1` で起動。本番向けの `config.json` を同梱するとよい。

本番連携（https://wl-ai-board.internal.wonder-link.co.jp/board/wl）を確認してから配布。詳細は wl-sticky-note の **`docs/AI-Board・Desktopアプリの開発の進め方.md`** を参照。

## ユーザー管理・Board System との共通化

- **ユーザーデータベース** … デスクトップアプリの「ボード」・パーソナルで利用するユーザーは、Board System の API（`/users/by_email` など）で解決する。Board System と Linko は同一の PostgreSQL の `users` テーブルを参照するため、**ユーザーは共通**である。
- **ユーザー登録** … 新規ユーザーは Board System 側で登録する（Board System の管理画面または API `POST /users`）。登録済みメールアドレスをデスクトップアプリの初回メール入力で入力すると、そのユーザーに紐づきパーソナルボードが開く。Linko と Board System で「同じ画面で登録」する場合は、Board System のユーザー管理画面を共通の登録窓口として利用する。

## 今後の拡張（開発プラン）
- AIボード・付箋ボードとの連携（受付モード切替時の通知など）

以下の機能は、付加価値のため優先度は低いが将来的に実装を考える
- 適切なタイミングでのニュース・付箋投稿の促し
- アバターの表示ウィンドウと自律動作
- 音声読み上げの実装
