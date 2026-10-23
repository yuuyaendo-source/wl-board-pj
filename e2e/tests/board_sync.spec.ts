import { test, expect } from '@playwright/test';

test.describe('Board System ↔ Postit Board Integration E2E', () => {

    test('付箋新規投稿から Task ボード自動配置のフロー', async ({ page }) => {
        // 1. Task ボード画面を開く
        await page.goto('/boards/taskboard');
        await expect(page.locator('h1, header')).toBeVisible();

        // 2. 1行入力コンポーネントから投稿
        const input = page.locator('input[placeholder*="付箋"], input[type="text"]').first();
        await input.fill('E2E テストタスク: 緊急報告書を作成する');
        await input.press('Enter');

        // 3. 画面上に新規付箋カードが表示されることを確認
        const noteCard = page.locator('text=E2E テストタスク: 緊急報告書を作成する');
        await expect(noteCard).toBeVisible({ timeout: 10000 });
    });

    test('Personal ボード DONE 移動から Task ボード完了(5)への連動', async ({ page }) => {
        // 1. パーソナルボード（所有者 1）を開く
        await page.goto('/boards/personal/1');

        // 2. ドラッグ対象の付箋が表示されることを確認
        const taskItem = page.locator('[data-note-id]').first();
        await expect(taskItem).toBeVisible({ timeout: 10000 });

        // 3. DONE ドロップゾーンの存在を明示的に検証した上でドラッグ操作を実行（条件分岐によるスキップを排除）
        const doneZone = page.locator('[data-lane="DONE"], text="DONE"').first();
        await expect(doneZone).toBeVisible({ timeout: 10000 });
        await taskItem.dragTo(doneZone);

        // 4. Task ボード側で連動状態（グレー化または quadrant 5）を確認
        await page.goto('/boards/taskboard');
        const completedTask = page.locator('.task-color-grey, [data-quadrant="5"]').first();
        await expect(completedTask).toBeVisible({ timeout: 10000 });
    });
});

test.describe('Sticky note business rules', () => {
    test('未完了の担当者がいる付箋は削除を拒否し、完了後は削除できる', async ({ request }) => {
        const apiBase = process.env.TEST_BACKEND_URL || 'http://localhost:8000';

        // 共有タスクを作成（personal_only: false）
        const created = await request.post(`${apiBase}/sticky_notes`, {
            data: { content: `E2E deletion rule ${Date.now()}`, author_id: 1, personal_only: false },
        });
        expect(created.status()).toBe(201);
        const note = await created.json();

        // 担当者（owner_id: 1）のパーソナルボードへ配置
        const assigned = await request.post(`${apiBase}/sticky_notes/${note.id}/move_to_personal`, {
            data: { owner_id: 1, lane: 'INBOX' },
        });
        expect(assigned.ok()).toBeTruthy();

        // 未完了の担当者がいるため削除は 400 でブロックされる
        const blockedDelete = await request.delete(`${apiBase}/sticky_notes/${note.id}`);
        expect(blockedDelete.status()).toBe(400);
        expect((await blockedDelete.json()).detail).toContain('完了');

        // タスクを完了状態に更新
        const completed = await request.patch(`${apiBase}/sticky_notes/${note.id}`, {
            data: { status: 'DONE' },
        });
        expect(completed.ok()).toBeTruthy();

        // 担当者が完了したため削除できる
        const allowedDelete = await request.delete(`${apiBase}/sticky_notes/${note.id}`);
        expect(allowedDelete.status()).toBe(204);
    });

    test('チームへ付箋を複数人コピーし、応援引き受けで依頼者のレーンを戻す', async ({ request }) => {
        const apiBase = process.env.TEST_BACKEND_URL || 'http://localhost:8000';

        // 共有タスクを作成
        const created = await request.post(`${apiBase}/sticky_notes`, {
            data: { content: `E2E team/help rule ${Date.now()}`, author_id: 1, personal_only: false },
        });
        expect(created.status()).toBe(201);
        const note = await created.json();

        try {
            // 所有者 1 のパーソナルボードへ配置
            await request.post(`${apiBase}/sticky_notes/${note.id}/move_to_personal`, {
                data: { owner_id: 1, lane: 'INBOX' },
            });

            // チームへ一括コピー
            const copied = await request.post(`${apiBase}/sticky_notes/${note.id}/copy_to_team`, {
                data: { team_id: 1 },
            });
            expect(copied.ok()).toBeTruthy();
            expect((await copied.json()).created).toBeGreaterThan(0);

            const placements = await request.get(`${apiBase}/board_placements?board_type=PERSONAL&owner_id=1`);
            const ownerPlacement = (await placements.json()).find((item: { note_id: number }) => item.note_id === note.id);
            expect(ownerPlacement).toBeTruthy();

            // 応援要請（HELP_REQUEST）に変更
            const helpRequest = await request.patch(`${apiBase}/board_placements/${ownerPlacement.id}`, {
                data: { lane: 'HELP_REQUEST' },
            });
            expect(helpRequest.ok()).toBeTruthy();

            // 別ユーザー（owner_id: 2）が引き受ける
            const accepted = await request.post(`${apiBase}/sticky_notes/${note.id}/move_to_personal`, {
                data: { owner_id: 2, lane: 'INBOX' },
            });
            expect(accepted.ok()).toBeTruthy();
            expect((await accepted.json()).lane).toBe('INBOX');

            // 依頼者（owner_id: 1）のレーンが INBOX に自動復帰していることを確認
            const requesterAfterAccept = await request.get(`${apiBase}/board_placements/${ownerPlacement.id}`);
            expect((await requesterAfterAccept.json()).lane).toBe('INBOX');
        } finally {
            await request.patch(`${apiBase}/sticky_notes/${note.id}`, { data: { status: 'DONE' } });
            await request.delete(`${apiBase}/sticky_notes/${note.id}`);
        }
    });
});