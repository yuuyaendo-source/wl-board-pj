# Wonder Rinko Desktop App (DT_APP)

社員PCに常駐する「Personal Rinko Agent」。**各ユーザー用のパーソナルモード**（`/personal?user=xxx`）へワンクリックで誘導し、お知らせからのDeep Linkを提供する。

## 機能

- **パーソナルモードを開く** … トレイの「パーソナルモードを開く」で、**このユーザー用**のパーソナル画面（AIボードの `/personal?user=ユーザーID`）をブラウザで開く。起動時に自動で開く動作は行わない。
- **システムトレイ常駐** … タスクトレイにアイコンを表示。**アイコンをクリック**すると設定した先（デフォルト: 付箋ボード）を開く。メニュー「アイコンクリックで開く」で付箋ボード／パーソナル／最後のお知らせを切り替え可能。
- **PC起動時に自動で起動** … メニュー「PC起動時に自動で起動」をONにすると、Windows ログイン時にアプリが自動起動し、タスクトレイに常駐する（レジストリのスタートアップに登録）。OFFで解除。
- **付箋ボード連携** … 付箋ボード（`postit_board_id`）を一定間隔でポーリングし、新付箋が増えたら「新しい付箋が投稿されました」とトースト。「最後のお知らせを開く」で該当ボードを開ける。
- **右下トーストお知らせ** … 業務の邪魔にならない位置に通知。**表示中にクリック**するとそのお知らせのURLへ飛べる。トレイの「最後のお知らせを開く」でも開ける。トーストの**アイコン**は `toast_icon_path` で変更可能（未設定時はトレイと同じ緑の丸デザイン）。
- **アバター表示/非表示** … メニューでトグル（設定のみ保存。アバター表示は今後実装）。
- **音声ON/OFF** … メニューでトグル。

## 必要な環境

- Windows 10/11（トーストは win10toast-click / win10toast。要 pywin32）
- Python 3.10+

## セットアップ・起動

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

**会社ポリシーにより exe の直接実行が不可**なため、配布は次のいずれかとします。

- **MSI 形式（推奨）** … Windows インストーラー（.msi）で配布。多くの企業ポリシーで許可され、インストール・アンインストールが標準で管理できる。`.\build_msi.ps1` でビルド。
- **フォルダ＋起動手順** … 本フォルダを ZIP で配布し、メンバーに Python 3.10+ と `.\start_app.ps1` での起動を依頼する。

## MSI ビルド（配布用）

```powershell
cd 02_3_WL_Desktop_app
.\build_msi.ps1
```

- 要: Python 3.10+（cx_Freeze を自動インストール）
- 出力: `dist\WonderRinko.msi`
- 配布: MSI を渡し、メンバーはダブルクリックでインストール。インストール先の `config.json` はビルド時に同梱したものが使われるため、**ビルド前に本番用の config.json を置いておく**とよい。

## 設定

- `config.json` … `user_id`、`personal_path`、**`postit_board_id`**（トレイクリックで開くデフォルトボード。本番: `wl`）、**`postit_board_ids`**（新付箋を監視するボードIDの配列。未設定時は `postit_board_id` のみ。複数指定でどのボードに付箋が追加されても通知）、`postit_poll_interval_sec`、**`tray_click_action`**、**`toast_icon_path`**、AIボードURL・付箋ボードURL（本番: `http://wl-sticky-note.local/`）、アバター・音声のON/OFFなど
- 環境変数 `WLINKO_USER_ID` でユーザーIDを指定可能。`AI_BOARD_URL`, `POSTIT_BOARD_URL` でURLを上書き可能（`.env` やシステム環境変数）

## 配布方法

- **MSI** … `.\build_msi.ps1` で `dist\WonderRinko.msi` を生成し配布。メンバーはインストーラーでインストール（Python 不要）。
- **フォルダ＋起動手順** … 本フォルダを ZIP で配布。メンバーは Python 3.10+ を入れ、`.\start_app.ps1` で起動。本番向けの `config.json` を同梱するとよい。

本番連携（http://wl-sticky-note.local/board/wl）を確認してから配布。詳細は wl-sticky-note の **`docs/AI-Board・Desktopアプリの開発の進め方.md`** を参照。

## 今後の拡張（開発プラン）
- AIボード・付箋ボードとの連携（受付モード切替時の通知など）

以下の機能は、付加価値のため優先度は低いが将来的に実装を考える
- 適切なタイミングでのニュース・付箋投稿の促し
- アバターの表示ウィンドウと自律動作
- 音声読み上げの実装
