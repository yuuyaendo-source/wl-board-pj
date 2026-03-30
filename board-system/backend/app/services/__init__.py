# -*- coding: utf-8 -*-
# orchestrator 等はサブモジュールから直接 import すること。
# ここで process_new_note_ai を読み込むと、client → llm_settings → services パッケージ初期化時に
# orchestrator → app.ai → client へ戻り循環インポートになる。
