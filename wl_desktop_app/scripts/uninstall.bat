@echo off
echo アプリを終了しています...
:: 通常終了要求（/f なし: WM_CLOSE を送信）
taskkill /im WonderLinko.exe >nul 2>&1
:: 3秒待機して atexit/Tkinterフック を走らせる
timeout /t 3 /nobreak >nul
:: 残っていれば強制終了
taskkill /f /im WonderLinko.exe >nul 2>&1

echo スタートアップのショートカットを削除しています...
:: ユーザーディレクトリを列挙して各プロファイルのショートカットを削除 (ワイルドカード制約回避)
FOR /D %%U IN ("C:\Users\*") DO (
    IF EXIST "%%U\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Wonder Linko.lnk" (
        del /Q "%%U\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Wonder Linko.lnk" >nul 2>&1
    )
)

echo アプリケーションをアンインストールしています...
:: wmic を使用してプロダクト名からサイレントアンインストールを実行
wmic product where "name='WonderLinkoDesktop'" call uninstall /nointeractive >nul 2>&1

echo アンインストールが完了しました。
pause