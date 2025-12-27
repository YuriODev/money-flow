"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { importExportApi, ImportResult, PdfSections, calendarApi, ICalFeedResponse, GoogleCalendarStatus } from "@/lib/api";
import StatementImportModal from "./StatementImportModal";

interface ImportExportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type TabType = "export" | "import" | "statement" | "calendar";

export default function ImportExportModal({ isOpen, onClose }: ImportExportModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>("export");
  const [includeInactive, setIncludeInactive] = useState(true);
  const [showStatementModal, setShowStatementModal] = useState(false);
  // PDF Report section options
  const [pdfSections, setPdfSections] = useState({
    categoryBreakdown: true,
    oneTimePayments: true,
    charts: true,
    upcomingPayments: true,
    paymentHistory: true,
    allPayments: true,
  });
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [calendarFeed, setCalendarFeed] = useState<ICalFeedResponse | null>(null);
  const [calendarLoading, setCalendarLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [googleStatus, setGoogleStatus] = useState<GoogleCalendarStatus | null>(null);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  // Fetch calendar feed URL and Google Calendar status when calendar tab is active
  useEffect(() => {
    if (activeTab === "calendar") {
      // Fetch iCal feed URL
      if (!calendarFeed && !calendarLoading) {
        setCalendarLoading(true);
        calendarApi.getICalFeedUrl()
          .then(setCalendarFeed)
          .catch((err) => setError(err.message))
          .finally(() => setCalendarLoading(false));
      }
      // Fetch Google Calendar status
      if (!googleStatus && !googleLoading) {
        setGoogleLoading(true);
        calendarApi.getGoogleCalendarStatus()
          .then(setGoogleStatus)
          .catch(() => {
            // Google Calendar may not be configured - that's ok
            setGoogleStatus({ connected: false, status: "not_connected", calendar_id: null, sync_enabled: null, last_sync_at: null, last_error: null });
          })
          .finally(() => setGoogleLoading(false));
      }
    }
  }, [activeTab, calendarFeed, calendarLoading, googleStatus, googleLoading]);

  const handleConnectGoogle = async () => {
    try {
      const response = await calendarApi.connectGoogleCalendar();
      // Redirect to Google OAuth
      window.location.href = response.authorization_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect Google Calendar");
    }
  };

  const handleDisconnectGoogle = async () => {
    try {
      await calendarApi.disconnectGoogleCalendar();
      setGoogleStatus({ connected: false, status: "disconnected", calendar_id: null, sync_enabled: null, last_sync_at: null, last_error: null });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to disconnect Google Calendar");
    }
  };

  const handleSyncGoogle = async () => {
    setSyncing(true);
    try {
      const result = await calendarApi.syncToGoogleCalendar();
      setError(null);
      alert(`Synced ${result.created} events to Google Calendar!`);
      // Refresh status
      const status = await calendarApi.getGoogleCalendarStatus();
      setGoogleStatus(status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to sync to Google Calendar");
    } finally {
      setSyncing(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Failed to copy to clipboard");
    }
  };

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

  const exportPdfMutation = useMutation({
    mutationFn: () => importExportApi.exportPdfAdvanced({
      includeInactive,
      sections: pdfSections,
    }),
    onSuccess: (blob) => {
      downloadFile(blob, `money_flow_report_${formatDate()}.pdf`);
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
    exportPdfMutation.isPending ||
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
          <button
            onClick={() => setActiveTab("statement")}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "statement"
                ? "text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
            }`}
          >
            Bank Statement
          </button>
          <button
            onClick={() => setActiveTab("calendar")}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === "calendar"
                ? "text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400"
                : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
            }`}
          >
            Calendar
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === "export" ? (
            <div className="space-y-4">
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                Export your subscriptions to a file for backup or transfer to another device.
              </p>

              {/* General Options */}
              <div className="space-y-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={includeInactive}
                    onChange={(e) => setIncludeInactive(e.target.checked)}
                    className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 dark:bg-gray-800 dark:checked:bg-blue-600"
                  />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Include inactive subscriptions</span>
                </label>
              </div>

              {/* PDF Report Sections */}
              <div className="mt-4 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <h4 className="text-sm font-medium text-purple-800 dark:text-purple-300 mb-2">PDF Report Sections</h4>
                <p className="text-xs text-purple-600 dark:text-purple-400 mb-3">Summary is always included. Choose additional sections:</p>
                <div className="grid grid-cols-2 gap-2">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={pdfSections.categoryBreakdown}
                      onChange={(e) => setPdfSections(prev => ({ ...prev, categoryBreakdown: e.target.checked }))}
                      className="rounded border-gray-300 dark:border-gray-600 text-purple-600 focus:ring-purple-500 dark:bg-gray-800 dark:checked:bg-purple-600"
                    />
                    <span className="text-xs text-gray-700 dark:text-gray-300">Categories</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={pdfSections.oneTimePayments}
                      onChange={(e) => setPdfSections(prev => ({ ...prev, oneTimePayments: e.target.checked }))}
                      className="rounded border-gray-300 dark:border-gray-600 text-purple-600 focus:ring-purple-500 dark:bg-gray-800 dark:checked:bg-purple-600"
                    />
                    <span className="text-xs text-gray-700 dark:text-gray-300">One-Time Payments</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={pdfSections.charts}
                      onChange={(e) => setPdfSections(prev => ({ ...prev, charts: e.target.checked }))}
                      className="rounded border-gray-300 dark:border-gray-600 text-purple-600 focus:ring-purple-500 dark:bg-gray-800 dark:checked:bg-purple-600"
                    />
                    <span className="text-xs text-gray-700 dark:text-gray-300">Charts</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={pdfSections.upcomingPayments}
                      onChange={(e) => setPdfSections(prev => ({ ...prev, upcomingPayments: e.target.checked }))}
                      className="rounded border-gray-300 dark:border-gray-600 text-purple-600 focus:ring-purple-500 dark:bg-gray-800 dark:checked:bg-purple-600"
                    />
                    <span className="text-xs text-gray-700 dark:text-gray-300">Upcoming Payments</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={pdfSections.paymentHistory}
                      onChange={(e) => setPdfSections(prev => ({ ...prev, paymentHistory: e.target.checked }))}
                      className="rounded border-gray-300 dark:border-gray-600 text-purple-600 focus:ring-purple-500 dark:bg-gray-800 dark:checked:bg-purple-600"
                    />
                    <span className="text-xs text-gray-700 dark:text-gray-300">Payment History</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={pdfSections.allPayments}
                      onChange={(e) => setPdfSections(prev => ({ ...prev, allPayments: e.target.checked }))}
                      className="rounded border-gray-300 dark:border-gray-600 text-purple-600 focus:ring-purple-500 dark:bg-gray-800 dark:checked:bg-purple-600"
                    />
                    <span className="text-xs text-gray-700 dark:text-gray-300">All Payments Table</span>
                  </label>
                </div>
              </div>

              {/* Export Buttons */}
              <div className="space-y-3">
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
                <button
                  onClick={() => exportPdfMutation.mutate()}
                  disabled={isLoading}
                  className="w-full bg-purple-600 hover:bg-purple-700 dark:bg-purple-600 dark:hover:bg-purple-700 text-white py-2 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>{exportPdfMutation.isPending ? "Generating Report..." : "Generate PDF Report"}</span>
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

          {/* Statement Import Tab */}
          {activeTab === "statement" && (
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                  <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">Smart Import from Bank Statements</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Upload your bank statement and we&apos;ll automatically detect recurring payments using AI.
                  </p>
                </div>
              </div>

              <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">Supported Formats</h4>
                <div className="flex flex-wrap gap-2">
                  {[
                    { ext: "PDF", color: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" },
                    { ext: "CSV", color: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" },
                    { ext: "OFX", color: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400" },
                    { ext: "QFX", color: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400" },
                    { ext: "QIF", color: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400" },
                  ].map(({ ext, color }) => (
                    <span key={ext} className={`px-2 py-1 text-xs font-medium rounded ${color}`}>
                      .{ext.toLowerCase()}
                    </span>
                  ))}
                </div>
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">How it works</h4>
                <ol className="text-sm text-blue-800 dark:text-blue-200 space-y-1 list-decimal list-inside">
                  <li>Upload your bank statement file</li>
                  <li>AI analyzes transactions for recurring patterns</li>
                  <li>Review and select subscriptions to import</li>
                  <li>Optionally assign a card or category</li>
                </ol>
              </div>

              <button
                onClick={() => setShowStatementModal(true)}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg transition-colors font-medium flex items-center justify-center space-x-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                </svg>
                <span>Import Bank Statement</span>
              </button>
            </div>
          )}

          {/* Calendar Sync Tab */}
          {activeTab === "calendar" && (
            <div className="space-y-4 max-h-[60vh] overflow-y-auto">
              {/* Google Calendar OAuth Section */}
              <div className="bg-gradient-to-r from-red-50 to-yellow-50 dark:from-red-900/20 dark:to-yellow-900/20 rounded-lg p-4 border border-red-200 dark:border-red-800">
                <div className="flex items-start space-x-3">
                  <div className="w-10 h-10 rounded-full bg-white dark:bg-gray-800 flex items-center justify-center shrink-0 shadow-sm">
                    <svg className="w-6 h-6" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h3 className="font-medium text-gray-900 dark:text-gray-100">Google Calendar Sync</h3>
                      {googleStatus?.connected && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded-full">
                          Connected
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {googleStatus?.connected
                        ? "Your subscriptions are synced to Google Calendar"
                        : "Connect to automatically sync payments to your Google Calendar"}
                    </p>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {googleLoading ? (
                    <div className="flex items-center space-x-2 text-gray-500">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></div>
                      <span className="text-sm">Loading...</span>
                    </div>
                  ) : googleStatus?.connected ? (
                    <>
                      <button
                        onClick={handleSyncGoogle}
                        disabled={syncing}
                        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm disabled:opacity-50"
                      >
                        {syncing ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            <span>Syncing...</span>
                          </>
                        ) : (
                          <>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            <span>Sync Now</span>
                          </>
                        )}
                      </button>
                      <button
                        onClick={handleDisconnectGoogle}
                        className="flex items-center space-x-2 px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg transition-colors text-sm"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        <span>Disconnect</span>
                      </button>
                      {googleStatus.last_sync_at && (
                        <span className="text-xs text-gray-500 dark:text-gray-400 self-center">
                          Last synced: {new Date(googleStatus.last_sync_at).toLocaleString()}
                        </span>
                      )}
                    </>
                  ) : (
                    <button
                      onClick={handleConnectGoogle}
                      className="flex items-center space-x-2 px-4 py-2 bg-white hover:bg-gray-50 dark:bg-gray-800 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 rounded-lg transition-colors text-sm shadow-sm"
                    >
                      <svg className="w-4 h-4" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                      </svg>
                      <span>Connect Google Calendar</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Divider */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200 dark:border-gray-700"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400">or use calendar subscription</span>
                </div>
              </div>

              {/* Original Calendar Subscription Section */}
              <div className="flex items-start space-x-3">
                <div className="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center shrink-0">
                  <svg className="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">Calendar Subscription (iCal)</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Subscribe to your payment calendar feed (read-only, auto-updates).
                  </p>
                </div>
              </div>

              {calendarLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                </div>
              ) : calendarFeed ? (
                <>
                  {/* Feed URL */}
                  <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">Your Calendar Feed URL</h4>
                    <div className="flex items-center space-x-2">
                      <input
                        type="text"
                        readOnly
                        value={calendarFeed.feed_url}
                        className="flex-1 text-xs bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded px-3 py-2 text-gray-700 dark:text-gray-300 font-mono"
                      />
                      <button
                        onClick={() => copyToClipboard(calendarFeed.feed_url)}
                        className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded transition-colors text-sm"
                      >
                        {copied ? "Copied!" : "Copy"}
                      </button>
                    </div>
                  </div>

                  {/* One-click subscribe */}
                  <a
                    href={calendarFeed.webcal_url}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 px-4 rounded-lg transition-colors font-medium flex items-center justify-center space-x-2"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    <span>Subscribe with One Click</span>
                  </a>

                  {/* Instructions for different apps */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">Manual Setup Instructions</h4>

                    {/* Google Calendar */}
                    <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3">
                      <div className="flex items-center space-x-2 mb-1">
                        <svg className="w-4 h-4 text-red-600 dark:text-red-400" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12 0C5.372 0 0 5.373 0 12s5.372 12 12 12c6.627 0 12-5.373 12-12S18.627 0 12 0zm.14 19.018c-3.868 0-7-3.14-7-7.018 0-3.878 3.132-7.018 7-7.018 1.89 0 3.47.697 4.682 1.829l-1.974 1.978c-.517-.489-1.418-1.058-2.708-1.058-2.31 0-4.187 1.956-4.187 4.27 0 2.315 1.877 4.27 4.187 4.27 2.669 0 3.668-1.958 3.822-2.978h-3.822v-2.586h6.35c.063.352.098.72.098 1.112 0 4.089-2.738 7-6.448 7z"/>
                        </svg>
                        <span className="text-sm font-medium text-red-800 dark:text-red-300">Google Calendar</span>
                      </div>
                      <p className="text-xs text-red-700 dark:text-red-400">{calendarFeed.instructions.google_calendar}</p>
                    </div>

                    {/* Apple Calendar */}
                    <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-3">
                      <div className="flex items-center space-x-2 mb-1">
                        <svg className="w-4 h-4 text-gray-700 dark:text-gray-300" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/>
                        </svg>
                        <span className="text-sm font-medium text-gray-800 dark:text-gray-200">Apple Calendar</span>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">{calendarFeed.instructions.apple_calendar}</p>
                    </div>

                    {/* Outlook */}
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3">
                      <div className="flex items-center space-x-2 mb-1">
                        <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M7.88 12.04q0 .45-.11.87-.1.41-.33.74-.22.33-.58.52-.37.2-.87.2t-.85-.2q-.35-.21-.57-.55-.22-.33-.33-.75-.1-.42-.1-.86t.1-.87q.1-.43.34-.76.22-.34.59-.54.36-.2.87-.2t.86.2q.35.21.57.55.22.34.31.77.1.43.1.88zM24 12v9.38q0 .46-.33.8-.33.32-.8.32H7.13q-.46 0-.8-.33-.32-.33-.32-.8V18H1q-.41 0-.7-.3-.3-.29-.3-.7V7q0-.41.3-.7Q.58 6 1 6h6.5V2.55q0-.44.3-.75.3-.3.75-.3h12.9q.44 0 .75.3.3.3.3.75V12zm-6-8.25v3h3v-3zm0 4.5v3h3v-3zm0 4.5v1.83l3.05-1.83zm-5.25-9v3h3.75v-3zm0 4.5v3h3.75v-3zm0 4.5v2.03l2.41 1.5 1.34-.8v-2.73zM9 3.75V6h2l.13.01.12.04v-2.3zM5.98 15.98q.9 0 1.6-.3.7-.32 1.19-.86.48-.55.73-1.28.25-.74.25-1.61 0-.83-.25-1.55-.24-.71-.71-1.24t-1.15-.83q-.68-.3-1.55-.3-.92 0-1.64.3-.71.3-1.2.85-.5.54-.75 1.3-.25.74-.25 1.63 0 .85.26 1.56.26.72.74 1.23.48.52 1.17.81.69.3 1.56.3zM7.5 21h12.39L12 16.08V17q0 .41-.3.7-.29.3-.7.3H7.5zm15-.13v-7.24l-5.9 3.54Z"/>
                        </svg>
                        <span className="text-sm font-medium text-blue-800 dark:text-blue-300">Outlook</span>
                      </div>
                      <p className="text-xs text-blue-700 dark:text-blue-400">{calendarFeed.instructions.outlook}</p>
                    </div>
                  </div>

                  {/* Features info */}
                  <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-indigo-900 dark:text-indigo-100 mb-2">What you get</h4>
                    <ul className="text-sm text-indigo-800 dark:text-indigo-200 space-y-1 list-disc list-inside">
                      <li>All upcoming payment dates in your calendar</li>
                      <li>Automatic updates when you add or modify subscriptions</li>
                      <li>Reminders 1 day before each payment</li>
                      <li>Payment amounts shown in event titles</li>
                    </ul>
                  </div>
                </>
              ) : (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  Failed to load calendar feed. Please try again.
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

      {/* Statement Import Modal */}
      <StatementImportModal
        isOpen={showStatementModal}
        onClose={() => {
          setShowStatementModal(false);
          // Optionally close the parent modal after import
          // onClose();
        }}
      />
    </div>
  );
}
