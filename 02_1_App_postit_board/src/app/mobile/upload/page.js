"use client";

import { useState } from 'react';
import styles from './page.module.css';

export default function MobileUploadPage() {
    const [isUploading, setIsUploading] = useState(false);
    const [message, setMessage] = useState(null);

    const handleFileChange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setIsUploading(true);
        setMessage(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Next.jsのRewrite機能を使ってPythonサーバーへ転送
            // これにより、スマホからでもPC上のPythonサーバー(localhost:5000)にアクセス可能になります
            const response = await fetch('/api/proxy/upload_image', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                setMessage({ type: 'success', text: 'ボードに送信しました！' });
            } else {
                setMessage({ type: 'error', text: '送信に失敗しました。' });
            }
        } catch (error) {
            console.error('Upload error:', error);
            setMessage({ type: 'error', text: '通信エラーが発生しました。' });
        } finally {
            setIsUploading(false);
            // inputをリセットするためにフォームをリセットするなどの処理が必要ですが、
            // Reactではkeyを変えるなどのハックが一般的。今回は簡易実装。
            e.target.value = '';
        }
    };

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>付箋アップロード</h1>
            
            <div className={styles.cameraContainer}>
                <label className={styles.cameraButton}>
                    {isUploading ? (
                        <div className={styles.spinner}></div>
                    ) : (
                        <>
                            📷 カメラを起動
                            <input
                                type="file"
                                accept="image/*"
                                capture="environment"
                                onChange={handleFileChange}
                                className={styles.hiddenInput}
                                disabled={isUploading}
                            />
                        </>
                    )}
                </label>
            </div>

            {message && (
                <div className={`${styles.toast} ${styles[message.type]}`}>
                    {message.text}
                </div>
            )}
        </div>
    );
}
