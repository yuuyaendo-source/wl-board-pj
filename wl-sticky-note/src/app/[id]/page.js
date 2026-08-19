// wl-sticky-note/src/app/[id]/page.js
import { redirect } from "next/navigation";

export default async function ShortUrlRedirect({ params }) {
    const { id } = await params;
    // /board/[id] へ自動転送
    redirect(`/board/${id}`);
}