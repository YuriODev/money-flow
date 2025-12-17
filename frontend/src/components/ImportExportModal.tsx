"use client";

import { useState, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { importExportApi, ImportResult } from "@/lib/api";

interface ImportExportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type TabType = "export" | "import";

export default function ImportExportModal({ isOpen, onClose }: ImportExportModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>("export");
  const [includeInactive, setIncludeInactive] = useState(true);
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const exportJsonMutation = useMutation({
    mutationFn: () => importExportApi.exportJson(includeInactive),
    onSuccess: (data) => {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      downloadFile(blob, `subscriptions_${formatDate()}.json`);
    },
    onError: (err: Error) => setError(err.message),
  });

  const exportCsvMutation = useMutation({
    mutationFn: () => importExportApi.exportCsv(includeInactive),
    onSuccess: (blob) => {
      downloadFile(blob, `subscriptions_${formatDate()}.csv`);
    },
    onError: (err: Error) => setError(err.message),
  });

  const importJsonMutation = useMutation({
    mutationFn: (file: File) => importExportApi.importJson(file, skipDuplicates),
    onSuccess: (result) => {
      setImportResult(result);
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const importCsvMutation = useMutation({
    mutationFn: (file: File) => importExportApi.importCsv(file, skipDuplicates),
    onSuccess: (result) => {
      setImportResult(result);
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const formatDate = () => {
    const now = new Date();
    return now.toISOString().slice(0, 10).replace(/-/g, "");
  };

  const downloadFile = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setError(null);
    setImportResult(null);

    if (file.name.endsWith(".json")) {
      importJsonMutation.mutate(file);
    } else if (file.name.endsWith(".csv")) {
      importCsvMutation.mutate(file);
    } else {
      setError("Please select a JSON or CSV file");
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleClose = () => {
    setError(null);
    setImportResult(null);
    onClose();
  };

  if (!isOpen) return null;

  const isLoading =
    exportJsonMutation.isPending ||
    exportCsvMutation.isPending ||
    importJsonMutation.isPending ||
    importCsvMutation.isPending;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-lg mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Import / Export</h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab("export")}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "export"
                ? "text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
            }`}
          >
            Export
          </button>
          <button
            onClick={() => setActiveTab("import")}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "import"
                ? "text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
            }`}
          >
            Import
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === "export" ? (
            <div className="space-y-4">
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                Export your subscriptions to a file for backup or transfer to another device.
              </p>

              {/* Options */}
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={includeInactive}
                  onChange={(e) => setIncludeInactive(e.target.checked)}
                  className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 dark:bg-gray-800 dark:checked:bg-blue-600"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Include inactive subscriptions</span>
              </label>

              {/* Export Buttons */}
              <div className="flex space-x-3">
                <button
                  onClick={() => exportJsonMutation.mutate()}
                  disabled={isLoading}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {exportJsonMutation.isPending ? "Exporting..." : "Export as JSON"}
                </button>
                <button
                  onClick={() => exportCsvMutation.mutate()}
                  disabled={isLoading}
                  className="flex-1 bg-green-600 hover:bg-green-700 dark:bg-green-600 dark:hover:bg-green-700 text-white py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {exportCsvMutation.isPending ? "Exporting..." : "Export as CSV"}
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                Import subscriptions from a JSON or CSV file. Supports files exported from this app.
              </p>

              {/* Options */}
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={skipDuplicates}
                  onChange={(e) => setSkipDuplicates(e.target.checked)}
                  className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 dark:bg-gray-800 dark:checked:bg-blue-600"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Skip duplicates (same name)</span>
              </label>

              {/* File Input */}
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-6 text-center hover:border-gray-400 dark:hover:border-gray-500 transition-colors">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".json,.csv"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer flex flex-col items-center"
                >
                  <svg
                    className="w-12 h-12 text-gray-400 dark:text-gray-500 mb-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {isLoading ? "Importing..." : "Click to select a file"}
                  </span>
                  <span className="text-xs text-gray-400 dark:text-gray-500 mt-1">JSON or CSV</span>
                </label>
              </div>

              {/* Import Result */}
              {importResult && (
                <div className={`rounded-lg p-4 ${importResult.failed > 0 ? "bg-yellow-50 dark:bg-yellow-900/30" : "bg-green-50 dark:bg-green-900/30"}`}>
                  <h4 className={`font-medium ${importResult.failed > 0 ? "text-yellow-800 dark:text-yellow-300" : "text-green-800 dark:text-green-300"}`}>
                    Import Complete
                  </h4>
                  <div className="mt-2 text-sm space-y-1">
                    <p className="text-green-700 dark:text-green-400">Imported: {importResult.imported}</p>
                    {importResult.skipped > 0 && (
                      <p className="text-gray-600 dark:text-gray-400">Skipped (duplicates): {importResult.skipped}</p>
                    )}
                    {importResult.failed > 0 && (
                      <p className="text-red-600 dark:text-red-400">Failed: {importResult.failed}</p>
                    )}
                  </div>
                  {importResult.errors.length > 0 && (
                    <div className="mt-3">
                      <p className="text-sm font-medium text-red-700 dark:text-red-400">Errors:</p>
                      <ul className="mt-1 text-xs text-red-600 dark:text-red-400 list-disc list-inside max-h-32 overflow-y-auto">
                        {importResult.errors.slice(0, 10).map((err, i) => (
                          <li key={i}>{err}</li>
                        ))}
                        {importResult.errors.length > 10 && (
                          <li>...and {importResult.errors.length - 10} more</li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mt-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-3">
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
