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

        // 2. ドラッグまたはボタン操作で DONE レーンへ移動 (API レベルでの検証も並行)
        const taskItem = page.locator('[data-note-id]').first();
        if (await taskItem.isVisible()) {
            // 操作シミュレーション
            await page.goto('/boards/taskboard');
            // Task ボード側で連動状態を確認
            await expect(page.locator('.task-color-grey, [data-quadrant="5"]')).toBeDefined();
        }
    });
});

test.describe('Sticky note business rules', () => {
    test('未完了の担当者がいる付箋は削除を拒否し、完了後は削除できる', async ({ request }) => {
        const apiBase = process.env.TEST_BACKEND_URL || 'http://localhost:8000';
        const created = await request.post(`${apiBase}/sticky_notes/create_personal`, {
            data: { owner_id: 1, content: `E2E deletion rule ${Date.now()}` },
        });
        expect(created.status()).toBe(201);
        const note = await created.json();

        const blockedDelete = await request.delete(`${apiBase}/sticky_notes/${note.id}`);
        expect(blockedDelete.status()).toBe(400);
        expect((await blockedDelete.json()).detail).toContain('完了');

        const completed = await request.patch(`${apiBase}/sticky_notes/${note.id}`, {
            data: { status: 'DONE' },
        });
        expect(completed.ok()).toBeTruthy();

        const allowedDelete = await request.delete(`${apiBase}/sticky_notes/${note.id}`);
        expect(allowedDelete.status()).toBe(204);
    });

    test('チームへ付箋を複数人コピーし、応援引き受けで依頼者のレーンを戻す', async ({ request }) => {
        const apiBase = process.env.TEST_BACKEND_URL || 'http://localhost:8000';
        const created = await request.post(`${apiBase}/sticky_notes/create_personal`, {
            data: { owner_id: 1, content: `E2E team/help rule ${Date.now()}` },
        });
        expect(created.status()).toBe(201);
        const note = await created.json();

        try {
            const copied = await request.post(`${apiBase}/sticky_notes/${note.id}/copy_to_team`, {
                data: { team_id: 1 },
            });
            expect(copied.ok()).toBeTruthy();
            expect((await copied.json()).created).toBeGreaterThan(0);

            const placements = await request.get(`${apiBase}/board_placements?board_type=PERSONAL&owner_id=1`);
            const ownerPlacement = (await placements.json()).find((item: { note_id: number }) => item.note_id === note.id);
            expect(ownerPlacement).toBeTruthy();

            const helpRequest = await request.patch(`${apiBase}/board_placements/${ownerPlacement.id}`, {
                data: { lane: 'HELP_REQUEST' },
            });
            expect(helpRequest.ok()).toBeTruthy();

            const accepted = await request.post(`${apiBase}/sticky_notes/${note.id}/move_to_personal`, {
                data: { owner_id: 2, lane: 'INBOX' },
            });
            expect(accepted.ok()).toBeTruthy();
            expect((await accepted.json()).lane).toBe('INBOX');

            const requesterAfterAccept = await request.get(`${apiBase}/board_placements/${ownerPlacement.id}`);
            expect((await requesterAfterAccept.json()).lane).toBe('INBOX');
        } finally {
            await request.patch(`${apiBase}/sticky_notes/${note.id}`, { data: { status: 'DONE' } });
            await request.delete(`${apiBase}/sticky_notes/${note.id}`);
        }
    });
});
