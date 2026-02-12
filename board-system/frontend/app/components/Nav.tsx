"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRef, useEffect, useState } from "react";
import { PERSONAL_MEMBERS } from "@/lib/personalMembers";

const links = [
  { href: "/task", label: "Task" },
  { href: "/morning", label: "Meeting" },
];

// 付箋ボードは /board/wl へ（Board System からのみ行き来）
const STICKY_BOARD_WL_URL =
  (process.env.NEXT_PUBLIC_LEGACY_BOARD_URL || "http://localhost:3000") + "/board/wl";

export default function Nav() {
  const pathname = usePathname();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const isPersonalPage = pathname?.startsWith("/personal/");

  return (
    <nav className="flex flex-wrap items-center gap-2 border-b border-[var(--border)] bg-white px-4 py-2 shadow-sm">
      <Link
        href="/task"
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
            {PERSONAL_MEMBERS.map(({ slug, name }) => (
              <li key={slug}>
                <Link
                  href={`/personal/${slug}`}
                  className="block px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-100"
                  onClick={() => setDropdownOpen(false)}
                >
                  {name}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      <a
        href={STICKY_BOARD_WL_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="ml-auto rounded-xl px-3 py-1.5 text-sm text-zinc-500 hover:bg-zinc-100 hover:text-zinc-700"
      >
        付箋ボード
      </a>
    </nav>
  );
}
