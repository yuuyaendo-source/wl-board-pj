"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

let authCallbackQueue: Array<(token: string) => void> = [];

export function requireAdminAuth(onSuccess: () => void) {
    if (typeof window !== "undefined") {
        const token = sessionStorage.getItem("admin_token");
        if (token) {
            onSuccess();
        } else {
            authCallbackQueue.push(onSuccess);
            window.dispatchEvent(new Event("auth-required"));
        }
    }
}

export default function AdminAuthModal() {
    const [isOpen, setIsOpen] = useState(false);
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const handleRequired = () => {
            setIsOpen(true);
            setError("");
            setPassword("");
        };
        const handleUnauthorized = () => {
            setError("セッションが切れました。再度パスワードを入力してください。");
            setIsOpen(true);
        };

        window.addEventListener("auth-required", handleRequired);
        window.addEventListener("auth-unauthorized", handleUnauthorized);

        return () => {
            window.removeEventListener("auth-required", handleRequired);
            window.removeEventListener("auth-unauthorized", handleUnauthorized);
        };
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const res = await api.admin.login(password);
            sessionStorage.setItem("admin_token", res.access_token);
            setIsOpen(false);

            const callbacks = [...authCallbackQueue];
            authCallbackQueue = [];
            callbacks.forEach((cb) => cb(res.access_token));
        } catch (err) {
            setError("パスワードが間違っています。");
        } finally {
            setLoading(false);
        }
    };

    const handleCancel = () => {
        setIsOpen(false);
        authCallbackQueue = [];
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm px-4">
            <div className="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl">
                <h2 className="mb-2 text-xl font-bold text-zinc-800">管理者認証</h2>
                <p className="mb-4 text-sm text-zinc-600">
                    この操作を実行するには、管理者パスワードを入力してください。
                </p>
                <form onSubmit={handleSubmit}>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="パスワード"
                        className="w-full rounded-lg border border-zinc-300 px-3 py-2 text-zinc-900 focus:border-[var(--primary)] focus:outline-none"
                        autoFocus
                    />
                    {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
                    <div className="mt-6 flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={handleCancel}
                            className="rounded-lg px-4 py-2 text-sm font-medium text-zinc-600 hover:bg-zinc-100"
                        >
                            キャンセル
                        </button>
                        <button
                            type="submit"
                            disabled={loading || !password}
                            className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-bold text-white hover:opacity-90 disabled:opacity-50"
                        >
                            {loading ? "認証中..." : "認証"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}