import { redirect } from "next/navigation";

export default async function ShortUrlRedirect({ params }) {
    const { id } = await params;
    // basePath ("/board") は Next.js が自動補完するため、`/${id}` を指定します
    redirect(`/${id}`);
}