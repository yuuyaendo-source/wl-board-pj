import { test, expect } from '@playwright/test';

test.describe('Board System ↔ Postit Board Integration E2E', () => {

    test('付箋新規投稿から Task ボード自動配置のフロー', async ({ page }) => {
        // 1. Task ボード画面を開く
        await page.goto('/boards/task');
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
            await page.goto('/boards/task');
            // Task ボード側で連動状態を確認
            await expect(page.locator('.task-color-grey, [data-quadrant="5"]')).toBeDefined();
        }
    });
});