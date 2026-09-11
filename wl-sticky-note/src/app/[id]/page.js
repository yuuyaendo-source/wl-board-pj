// wl-sticky-note/src/app/[id]/page.js
import { redirect } from "next/navigation";

export default async function ShortUrlRedirect({ params }) {
    const { id } = await params;
    // id が "board" の場合に /board/board へ二重リダイレクトされるのを防止します
    if (id === "board") {
        redirect("/board/wl");
    }
    // /board/[id] へ自動転送
    redirect(`/board/${id}`);
}