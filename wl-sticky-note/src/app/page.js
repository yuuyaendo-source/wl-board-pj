import { redirect } from "next/navigation";

// トップはデフォルトボードへ（basePath 時は /board/wl、開発時は /board/wl）
export default function Home() {
  const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";
  redirect(basePath ? `${basePath}/wl` : "/board/wl");
}
