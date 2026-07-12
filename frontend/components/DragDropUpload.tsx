"use client";

import { useCallback, useRef, useState } from "react";
import { uploadDocuments, ApiError } from "@/lib/api";

const SUPPORTED = [".pdf", ".md", ".txt", ".docx", ".html", ".htm", ".csv"];

interface UploadFileEntry {
  file: File;
  status: "pending" | "uploading" | "done" | "error";
  error?: string;
}

export function DragDropUpload() {
  const [files, setFiles] = useState<UploadFileEntry[]>([]);
  const [dragging, setDragging] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [resultType, setResultType] = useState<"success" | "error">("success");
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((incoming: FileList | File[]) => {
    const entries: UploadFileEntry[] = Array.from(incoming)
      .filter((f) => SUPPORTED.includes(f.name.toLowerCase().slice(f.name.lastIndexOf("."))))
      .map((f) => ({ file: f, status: "pending" as const }));
    setFiles((prev) => [...prev, ...entries]);
    setResult(null);
    setResultType("success");
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      if (e.dataTransfer.files.length > 0) addFiles(e.dataTransfer.files);
    },
    [addFiles],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragging(false), []);

  const handleUpload = async () => {
    const pending = files.filter((f) => f.status === "pending");
    if (pending.length === 0) return;

    setFiles((prev) => prev.map((f) => (f.status === "pending" ? { ...f, status: "uploading" } : f)));
    setResult(null);

    try {
      const res = await uploadDocuments(pending.map((f) => f.file));
      setFiles((prev) => prev.map((f) => (f.status === "uploading" ? { ...f, status: "done" } : f)));
      setResult(res.message);
      setResultType("success");
    } catch (err) {
      setFiles((prev) => prev.map((f) => (f.status === "uploading" ? { ...f, status: "error", error: String(err) } : f)));
      setResult(err instanceof ApiError ? err.message : "Upload failed");
      setResultType("error");
    }
  };

  const clearFiles = () => {
    setFiles([]);
    setResult(null);
    setResultType("success");
  };

  return (
    <div className="flex flex-col gap-4">
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-card border-2 border-dashed p-8 text-center transition-colors ${
          dragging
            ? "border-tab bg-tab-soft"
            : "border-rule bg-card hover:border-tab/50"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={SUPPORTED.join(",")}
          className="hidden"
          onChange={(e) => e.target.files && addFiles(e.target.files)}
        />
        <span className="font-display text-lg text-ink">
          {dragging ? "Drop files here" : "Drag & drop files here"}
        </span>
        <span className="font-sans text-xs text-ink-muted">
          or click to browse &middot; {SUPPORTED.join(", ")}
        </span>
      </div>

      {files.length > 0 && (
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs uppercase tracking-widest text-ink-muted">
              {files.length} file(s)
            </span>
            <button
              type="button"
              onClick={clearFiles}
              className="font-mono text-xs text-rejected hover:underline"
            >
              Clear
            </button>
          </div>
          <ul className="flex flex-col gap-1">
            {files.map((entry, i) => (
              <li
                key={`${entry.file.name}-${i}`}
                className="flex items-center gap-3 rounded-card border border-rule bg-card px-3 py-2 font-sans text-sm"
              >
                <span className="flex-1 truncate text-ink">{entry.file.name}</span>
                <span className="text-xs text-ink-muted">{(entry.file.size / 1024).toFixed(0)} KB</span>
                {entry.status === "pending" && (
                  <span className="text-xs text-tab">pending</span>
                )}
                {entry.status === "uploading" && (
                  <span className="text-xs text-tab">uploading…</span>
                )}
                {entry.status === "done" && (
                  <span className="text-xs text-grounded">&#10003;</span>
                )}
                {entry.status === "error" && (
                  <span className="text-xs text-rejected" title={entry.error}>
                    failed
                  </span>
                )}
              </li>
            ))}
          </ul>
          {files.some((f) => f.status === "pending") && (
            <button
              type="button"
              onClick={handleUpload}
              className="self-start rounded-card bg-ink px-6 py-2 font-mono text-sm font-medium text-paper transition-opacity hover:opacity-90"
            >
              Upload &amp; index
            </button>
          )}
        </div>
      )}

      {result && (
        <div className={`rounded-card border px-4 py-3 ${
          resultType === "error"
            ? "border-rejected/40 bg-red-50"
            : "border-grounded/40 bg-grounded-soft"
        }`}>
          <p className={`font-mono text-xs uppercase tracking-widest ${
            resultType === "error" ? "text-rejected" : "text-grounded"
          }`}>{resultType === "error" ? "Error" : "Done"}</p>
          <p className="mt-1 font-sans text-sm text-ink">{result}</p>
        </div>
      )}
    </div>
  );
}
