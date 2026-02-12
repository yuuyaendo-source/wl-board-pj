"use client";

import { useParams } from "next/navigation";
import { getMemberBySlug } from "@/lib/personalMembers";
import PersonalBoardView from "../../components/PersonalBoardView";

export default function PersonalSlugPage() {
  const params = useParams();
  const slug = typeof params.slug === "string" ? params.slug : "";
  const member = getMemberBySlug(slug);

  if (!member) {
    return (
      <div className="p-6">
        <p className="text-zinc-600 dark:text-zinc-400">指定のメンバーが見つかりません。</p>
      </div>
    );
  }

  return (
    <PersonalBoardView ownerId={member.ownerId} displayName={member.name} />
  );
}
