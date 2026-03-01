"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

/** パーソナルボード用メンバー（URL の slug は user.id を文字列にしたもの） */
export interface PersonalMember {
  slug: string;
  ownerId: number;
  name: string;
  email?: string | null;
  call_name?: string | null;
}

/** API の /users からメンバー一覧を取得。メンバー増減に対応する */
export function usePersonalMembers(): {
  members: PersonalMember[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
} {
  const [members, setMembers] = useState<PersonalMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const users = await api.users.list();
      setMembers(
        users.map((u) => ({
          slug: String(u.id),
          ownerId: u.id,
          name: u.name,
          email: u.email ?? undefined,
          call_name: u.call_name ?? undefined,
        }))
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load members");
      setMembers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { members, loading, error, refetch };
}

export function getMemberBySlug(
  slug: string,
  members: PersonalMember[]
): { ownerId: number; name: string } | null {
  const m = members.find((x) => x.slug === slug);
  return m ? { ownerId: m.ownerId, name: m.name } : null;
}
