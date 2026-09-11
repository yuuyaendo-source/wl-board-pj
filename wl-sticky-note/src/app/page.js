import { redirect } from "next/navigation";

// トップはデフォルトボードへ（basePath 時は /board/wl、開発時は /board/wl）
export default function Home() {
  redirect("/board/wl");
}