import { redirect } from "next/navigation";

/** 旧URL /task を /taskboard へリダイレクト（本番で /task が 404 になったためルート名を taskboard に変更） */
export default function TaskRedirect() {
  redirect("/taskboard");
}
