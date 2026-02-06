# Wonder Rinko Desktop App (DT_APP)

社員PCに常駐する「Personal Rinko Agent」。**各ユーザー用のパーソナルモード**（`/personal?user=xxx`）へワンクリックで誘導し、お知らせからのDeep Linkを提供する。

## 機能

- **パーソナルモードを開く** … トレイの「パーソナルモードを開く」で、**このユーザー用**のパーソナル画面（AIボードの `/personal?user=ユーザーID`）をブラウザで開く。起動時に自動で開く動作は行わない。
- **システムトレイ常駐** … タスクトレイにアイコンを表示。**アイコンをクリック**すると設定した先（デフォルト: 付箋ボード）を開く。メニュー「アイコンクリックで開く」で付箋ボード／パーソナル／最後のお知らせを切り替え可能。
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

## 設定

- `config.json` … `user_id`、`personal_path`、`postit_board_id`、`postit_poll_interval_sec`、**`tray_click_action`**（トレイアイコンクリックで開く先）、**`toast_icon_path`**（トースト用アイコン。PNG/ICO の絶対パス。空ならデフォルト）、AIボードURL・付箋ボードURL、アバター・音声のON/OFFなど
- 環境変数 `WLINKO_USER_ID` でユーザーIDを指定可能。`AI_BOARD_URL`, `POSTIT_BOARD_URL` でURLを上書き可能（`.env` やシステム環境変数）

## 今後の拡張（開発プラン）

- AIボード・付箋ボードとの連携（受付モード切替時の通知など）
- 適切なタイミングでのニュース・付箋投稿の促し
- アバターの表示ウィンドウと自律動作
- 音声読み上げの実装
