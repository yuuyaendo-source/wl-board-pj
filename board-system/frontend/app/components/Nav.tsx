"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRef, useEffect, useState } from "react";
import { usePersonalMembers } from "@/lib/personalMembers";
import AddUserMenu from "./AddUserMenu";

const links = [
  { href: "/taskboard", label: "Task" },
  { href: "/meeting", label: "Meeting" },
];

// 付箋ボードは /board/wl へ（Board System からのみ行き来）
const STICKY_BOARD_WL_URL =
  (process.env.NEXT_PUBLIC_LEGACY_BOARD_URL || "http://localhost:3000") + "/board/wl";

const AWARENESS_TRELLO_URL =
  "https://trello.com/b/VTKI9CBt/%E6%84%8F%E8%AD%98%E5%90%88%E3%82%8F%E3%81%9B";

const EVALUATION_WEB_URL = "https://wonder-link.japaneast.cloudapp.azure.com/login";

// 交通費精算（仮）リンク先は未定。URL が決まり次第ここを差し替えてください。
const TRAVEL_EXPENSE_URL = "https://transport.internal.wonder-link.com/";

const INTERNAL_STUDY_ARCHIVE_URL = "http://wl-internal-study.local/";

export default function Nav() {
  const pathname = usePathname();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [adminMenuOpen, setAdminMenuOpen] = useState(false);
  const [systemSubOpen, setSystemSubOpen] = useState(false);
  const [userPanelOpen, setUserPanelOpen] = useState(false);
  const adminRef = useRef<HTMLDivElement>(null);
  const { members: personalMembers, loading: membersLoading, refetch: refetchMembers } = usePersonalMembers();

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
      if (adminRef.current && !adminRef.current.contains(e.target as Node)) {
        setAdminMenuOpen(false);
        setSystemSubOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const isPersonalPage = pathname?.startsWith("/personal/");
  const isAdminPage = pathname?.startsWith("/admin/");

  return (
    <nav className="sticky top-0 z-20 flex flex-wrap items-center gap-2 border-b border-[var(--border)] bg-white px-4 py-2 shadow-sm">
      <Link
        href="/taskboard"
        className="rounded-xl px-3 py-1.5 font-medium text-zinc-700 hover:bg-zinc-100"
      >
        Board System
      </Link>
      {links.map(({ href, label }) => (
        <Link
          key={href}
          href={href}
          className={`rounded-xl px-3 py-1.5 font-medium transition-colors ${
            pathname === href
              ? "bg-[var(--primary)] text-white"
              : "text-zinc-600 hover:bg-zinc-100"
          }`}
        >
          {label}
        </Link>
      ))}
      <a
        href={AWARENESS_TRELLO_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="rounded-xl px-3 py-1.5 font-medium text-zinc-600 hover:bg-zinc-100"
      >
        意識合わせ
      </a>

      <div className="relative" ref={dropdownRef}>
        <button
          type="button"
          onClick={() => setDropdownOpen((o) => !o)}
          className={`rounded-xl px-3 py-1.5 font-medium transition-colors ${
            isPersonalPage ? "bg-[var(--primary)] text-white" : "text-zinc-600 hover:bg-zinc-100"
          }`}
          aria-haspopup="listbox"
          aria-expanded={dropdownOpen}
        >
          パーソナルボード ▾
        </button>
        {dropdownOpen && (
          <ul
            className="absolute left-0 top-full z-50 mt-1 min-w-[180px] list-none rounded-xl border border-[var(--border)] bg-white py-1 shadow-lg"
            role="listbox"
          >
            {membersLoading ? (
              <li className="px-4 py-2 text-sm text-zinc-500">読込中…</li>
            ) : (
              personalMembers.map(({ slug, name }) => (
                <li key={slug}>
                  <Link
                    href={`/personal/${slug}`}
                    className="block px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-100"
                    onClick={() => setDropdownOpen(false)}
                  >
                    {name}
                  </Link>
                </li>
              ))
            )}
          </ul>
        )}
      </div>
      <a
        href={EVALUATION_WEB_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="rounded-xl px-3 py-1.5 font-medium text-zinc-600 hover:bg-zinc-100"
      >
        評価WEB
      </a>

      <a
        href={TRAVEL_EXPENSE_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="rounded-xl px-3 py-1.5 font-medium text-zinc-600 hover:bg-zinc-100"
      >
        交通費精算
      </a>

      <a
        href={INTERNAL_STUDY_ARCHIVE_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="rounded-xl px-3 py-1.5 font-medium text-zinc-600 hover:bg-zinc-100"
      >
        社内勉強会サイト
      </a>

      <a
          href={STICKY_BOARD_WL_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-xl px-3 py-1.5 font-medium text-zinc-600 hover:bg-zinc-100"
        >
          付箋ボード
        </a>
      
      <div className="ml-auto flex items-center gap-2" ref={adminRef}>
        <div className="relative">
          <button
            type="button"
            onClick={() => setAdminMenuOpen((o) => !o)}
            className={`rounded-xl px-3 py-1.5 text-sm font-medium transition-colors ${
              isAdminPage || userPanelOpen ? "bg-zinc-200 text-zinc-800" : "text-zinc-600 hover:bg-zinc-100"
            }`}
            aria-haspopup="menu"
            aria-expanded={adminMenuOpen}
          >
            管理 ▾
          </button>
          {adminMenuOpen && (
            <ul
              className="absolute right-0 top-full z-50 mt-1 min-w-[220px] list-none rounded-xl border border-[var(--border)] bg-white py-1 shadow-lg"
              role="menu"
            >
              <li role="none">
                <button
                  type="button"
                  role="menuitem"
                  className="w-full px-4 py-2.5 text-left text-sm text-zinc-700 hover:bg-zinc-100"
                  onClick={() => {
                    setUserPanelOpen(true);
                    setAdminMenuOpen(false);
                    setSystemSubOpen(false);
                  }}
                >
                  ユーザー管理
                </button>
              </li>
              <li role="none" className="border-t border-[var(--border)]">
                <button
                  type="button"
                  role="menuitem"
                  className="flex w-full items-center justify-between px-4 py-2.5 text-left text-sm text-zinc-700 hover:bg-zinc-100"
                  onClick={() => setSystemSubOpen((s) => !s)}
                  aria-expanded={systemSubOpen}
                >
                  <span>システム管理</span>
                  <span className="text-zinc-400">{systemSubOpen ? "▾" : "▸"}</span>
                </button>
                {systemSubOpen && (
                  <ul className="list-none border-t border-[var(--border)] bg-zinc-50 py-1" role="menu">
                    <li role="none">
                      <Link
                        href="/admin/system#llm"
                        role="menuitem"
                        className="block px-4 py-2 pl-6 text-sm text-zinc-700 hover:bg-zinc-100"
                        onClick={() => {
                          setAdminMenuOpen(false);
                          setSystemSubOpen(false);
                        }}
                      >
                        LLM切替
                      </Link>
                    </li>
                  </ul>
                )}
              </li>
            </ul>
          )}
        </div>
        <AddUserMenu
          members={personalMembers}
          onSuccess={refetchMembers}
          open={userPanelOpen}
          onOpenChange={setUserPanelOpen}
        />
      </div>
    </nav>
  );
}
