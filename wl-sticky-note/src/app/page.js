import { redirect } from "next/navigation";

export default function Home() {
  // basePath ("/board") は Next.js が自動補完するため、単体で "/wl" を指定します
  redirect("/wl");
}