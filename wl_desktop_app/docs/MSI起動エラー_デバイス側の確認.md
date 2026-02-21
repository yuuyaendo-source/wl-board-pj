# MSI インストール後の起動エラー（デバイス側の確認）

「`ImportError: cannot import name '_imaging' from 'PIL'`」が出る場合、**デバイス（実行するPC）側**に原因がある可能性があります。

## 0. 「以前のインストールで残った .pyd」について

インストール先の `lib\PIL\_imaging.cp312-win_amd64.pyd` が**以前のアプリインストール時に置かれたもの**で、**今回の MSI には同梱されていない**場合があります。その場合、次で配布用 MSI を正しく作り直してください。

1. **ビルド環境**で `pip install Pillow` を実行し、Pillow が入っていることを確認する。
2. **`.\build_msi.ps1`** を実行する。  
   - ビルド完了時に「PIL _imaging: bundled (_imaging.cp312-win_amd64.pyd)」と出ていれば、この MSI には .pyd が含まれています。  
   - 「_imaging*.pyd が build に含まれていません」でエラーになる場合は、同梱漏れなので MSI を配布しないでください。
3. **インストール側**では、可能なら一度アンインストールしてから新しい MSI でクリーンインストールする。

---

## 1. 診断ログで確認する

MSI インストール後、一度でも exe を起動している場合、次のファイルが作成されています。

- **場所**: インストール先フォルダ（WonderLinko.exe と同じフォルダ）
- **ファイル名**: `WonderLinko_diagnostic.txt`

この中に次のような情報が書かれます。

- `exe_dir` … exe のフォルダ
- `lib_dir exists` … `lib` フォルダがあるか
- `lib/PIL exists` … `lib\PIL` フォルダがあるか
- `lib/PIL files` … `lib\PIL` 内のファイル一覧
- `_imaging*.pyd` … 必須の C 拡張ファイルが含まれているか
- PIL 読み込みに失敗した場合、そのエラー内容とデバイス側の確認ポイント

**確認してほしいこと**

- `lib/PIL exists: True` かつ `_imaging*.pyd` に 1 つ以上ファイル名が列挙されているか  
  → 含まれていなければ、ビルド／MSI の同梱ミスの可能性
- `lib/PIL exists: True` で `_imaging*.pyd` も列挙されているのにエラーになる  
  → デバイス側の要因が高い（下記 2〜4 を確認）

## 2. デバイス側で考えられる要因

| 要因 | 内容・対処 |
|------|------------|
| **Visual C++ Redistributable 未導入** | PIL の `_imaging.pyd` は C 拡張のため、Microsoft Visual C++ 再頒布パッケージが必要です。未導入の場合は [Microsoft の公式ページ](https://learn.microsoft.com/ja-jp/cpp/windows/latest-supported-vc-redist) から「x64」用をインストールして再起動し、exe を再度実行してください。 |
| **ウイルス対策・セキュリティ** | 一部のセキュリティソフトが `.pyd` を「不審な DLL」としてブロック・隔離することがあります。除外設定に「インストール先フォルダ」や「WonderLinko.exe」を追加するか、一時的に無効にして起動できるか試してください。 |
| **インストール先の権限** | インストール先（例: `%LocalAppData%\WonderLink\WonderLinko`）やその中の `lib\PIL` が読み取り不可・削除されていると失敗します。フォルダのプロパティで権限を確認し、`lib\PIL` に `_imaging*.pyd` が実際に存在するかも確認してください。 |
| **別 PC へのコピー** | MSI を別 PC にコピーしてインストールした場合、上記の VC++ Redist やセキュリティソフトの違いで、ビルドした PC では動いてもその PC では動かないことがあります。 |

## 3. 手動で確認する項目

1. **インストール先を開く**  
   例: ユーザー単位インストールなら  
   `C:\Users\<ユーザー名>\AppData\Local\WonderLink\WonderLinko`

2. **次のフォルダ・ファイルがあるか確認**
   - `lib` フォルダ
   - `lib\PIL` フォルダ
   - `lib\PIL\_imaging.cp3XX-win_amd64.pyd`（XX は Python のマイナーバージョン。例: 312）

3. **`_imaging*.pyd` が無い場合**  
   ビルド時の同梱漏れの可能性があります。`setup.py` の PIL の `include_files` と、ビルド出力の `build\...\lib\PIL\` に `.pyd` が含まれているか確認してください。

4. **`_imaging*.pyd` はあるのにエラーになる場合**  
   VC++ Redistributable のインストールと、ウイルス対策の除外設定を優先して確認してください。

## 4. まとめ

- **同じエラーが続く場合でも、デバイス側の要因は十分あり得ます。**
- 起動時に `WonderLinko_diagnostic.txt` が出力されるので、その内容で「同梱されているか」と「デバイス側か」を切り分けてください。
- エラー時にはメッセージボックスで上記の確認ポイントを案内します。
