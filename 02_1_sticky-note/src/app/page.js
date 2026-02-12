import { redirect } from "next/navigation";

// トップは /board/wl へ（next.config の redirect と二重で対応）
export default function Home() {
  redirect("/board/wl");
}
