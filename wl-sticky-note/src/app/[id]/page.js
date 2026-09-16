// src/app/[id]/page.js
import { redirect } from "next/navigation";

export default async function ShortUrlRedirect({ params }) {
    const { id } = await params;

    // 拡張子付きファイルや内部パスへのリクエストは無視する
    if (!id || id.includes(".") || id.startsWith("_")) {
        return null;
    }
    if (id === "board") {
        redirect("/board/wl");
    }
    redirect(`/board/${id}`);
}