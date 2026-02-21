import { redirect } from "next/navigation";

/** 旧URL /morning を /meeting へリダイレクト */
export default function MorningRedirect() {
  redirect("/meeting");
}
