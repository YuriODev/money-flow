"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  statementImportApi,
  banksApi,
  cardsApi,
  categoriesApi,
  BankProfile,
  ImportPreview,
  DetectedSubscription,
  ConfirmImportResponse,
  PaymentCard,
  Category,
  PAYMENT_TYPE_LABELS,
  PaymentType,
} from "@/lib/api";

interface StatementImportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type ImportStep = "upload" | "processing" | "preview" | "confirm" | "complete";

// Supported file extensions
const SUPPORTED_EXTENSIONS = [".pdf", ".csv", ".ofx", ".qfx", ".qif"];

// Frequency labels
const FREQUENCY_LABELS: Record<string, string> = {
  weekly: "Weekly",
  biweekly: "Bi-weekly",
  monthly: "Monthly",
  quarterly: "Quarterly",
  yearly: "Yearly",
};

// Confidence thresholds
const HIGH_CONFIDENCE = 0.8;
const LOW_CONFIDENCE = 0.5;

export default function StatementImportModal({
  isOpen,
  onClose,
}: StatementImportModalProps) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // State
  const [step, setStep] = useState<ImportStep>("upload");
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedBankId, setSelectedBankId] = useState<string>("");
  const [currency, setCurrency] = useState<string>("GBP");
  const [useAI, setUseAI] = useState<boolean>(true);
  const [jobId, setJobId] = useState<string | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [selectedCardId, setSelectedCardId] = useState<string>("");
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>("");
  const [importResult, setImportResult] = useState<ConfirmImportResponse | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [bankSearch, setBankSearch] = useState("");

  // Queries
  const { data: banks = [] } = useQuery({
    queryKey: ["banks"],
    queryFn: () => banksApi.getAll(),
    enabled: isOpen,
  });

  const { data: cards = [] } = useQuery({
    queryKey: ["cards"],
    queryFn: () => cardsApi.getAll(),
    enabled: isOpen && step === "preview",
  });

  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.getAll(),
    enabled: isOpen && step === "preview",
  });

  // Filter banks by search
  const filteredBanks = banks.filter(
    (bank) =>
      bank.name.toLowerCase().includes(bankSearch.toLowerCase()) ||
      bank.country_code.toLowerCase().includes(bankSearch.toLowerCase())
  );

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      return statementImportApi.uploadStatement(file, {
        bank_id: selectedBankId || undefined,
        currency,
        use_ai: useAI,
      });
    },
    onSuccess: (data) => {
      setJobId(data.job_id);
      setStep("processing");
      // Start polling for job status
      pollJobStatus(data.job_id);
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  // Poll job status
  const pollJobStatus = useCallback(async (id: string) => {
    const maxAttempts = 60; // 60 seconds max
    let attempts = 0;

    const poll = async () => {
      try {
        const status = await statementImportApi.getJobStatus(id);

        if (status.is_ready) {
          // Fetch preview
          const previewData = await statementImportApi.getPreview(id);
          setPreview(previewData);
          setStep("preview");
        } else if (status.status === "failed") {
          setError(status.error_message || "Processing failed");
          setStep("upload");
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 1000);
        } else {
          setError("Processing timed out. Please try again.");
          setStep("upload");
        }
      } catch (err) {
        setError((err as Error).message);
        setStep("upload");
      }
    };

    poll();
  }, []);

  // Toggle subscription selection
  const toggleSelection = useMutation({
    mutationFn: async ({
      id,
      isSelected,
    }: {
      id: string;
      isSelected: boolean;
    }) => {
      return statementImportApi.updateDetected(id, { is_selected: isSelected });
    },
    onSuccess: (updated) => {
      if (preview) {
        setPreview({
          ...preview,
          detected_subscriptions: preview.detected_subscriptions.map((sub) =>
            sub.id === updated.id ? updated : sub
          ),
          summary: {
            ...preview.summary,
            selected_count: preview.detected_subscriptions.filter((s) =>
              s.id === updated.id ? updated.is_selected : s.is_selected
            ).length,
          },
        });
      }
    },
  });

  // Select/deselect all
  const bulkUpdateMutation = useMutation({
    mutationFn: async (isSelected: boolean) => {
      if (!preview) return null;
      const ids = preview.detected_subscriptions
        .filter((s) => s.status !== "duplicate")
        .map((s) => s.id);
      return statementImportApi.bulkUpdateDetected(ids, { is_selected: isSelected });
    },
    onSuccess: (_, isSelected) => {
      if (preview) {
        setPreview({
          ...preview,
          detected_subscriptions: preview.detected_subscriptions.map((sub) =>
            sub.status !== "duplicate" ? { ...sub, is_selected: isSelected } : sub
          ),
          summary: {
            ...preview.summary,
            selected_count: isSelected
              ? preview.detected_subscriptions.filter((s) => s.status !== "duplicate").length
              : 0,
          },
        });
      }
    },
  });

  // Confirm import mutation
  const confirmMutation = useMutation({
    mutationFn: async () => {
      if (!jobId) throw new Error("No job ID");
      const selectedIds = preview?.detected_subscriptions
        .filter((s) => s.is_selected && s.status !== "duplicate")
        .map((s) => s.id);

      return statementImportApi.confirmImport(jobId, {
        subscription_ids: selectedIds,
        card_id: selectedCardId || undefined,
        category_id: selectedCategoryId || undefined,
      });
    },
    onSuccess: (result) => {
      setImportResult(result);
      setStep("complete");
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  // File handlers
  const handleFileSelect = (file: File) => {
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
    if (!SUPPORTED_EXTENSIONS.includes(ext)) {
      setError(`Unsupported file type. Supported: ${SUPPORTED_EXTENSIONS.join(", ")}`);
      return;
    }
    setSelectedFile(file);
    setError(null);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelect(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileSelect(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  // Start upload
  const handleUpload = () => {
    if (!selectedFile) {
      setError("Please select a file");
      return;
    }
    uploadMutation.mutate(selectedFile);
  };

  // Reset and close
  const handleClose = () => {
    setStep("upload");
    setError(null);
    setSelectedFile(null);
    setSelectedBankId("");
    setCurrency("GBP");
    setUseAI(true);
    setJobId(null);
    setPreview(null);
    setSelectedCardId("");
    setSelectedCategoryId("");
    setImportResult(null);
    setBankSearch("");
    onClose();
  };

  // Get confidence badge color
  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= HIGH_CONFIDENCE) {
      return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
    } else if (confidence >= LOW_CONFIDENCE) {
      return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400";
    }
    return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
  };

  if (!isOpen) return null;

  const isLoading = uploadMutation.isPending || confirmMutation.isPending;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-3xl mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 shrink-0">
          <div className="flex items-center space-x-3">
            <svg
              className="w-6 h-6 text-blue-600 dark:text-blue-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
              Import Bank Statement
            </h2>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center p-4 border-b border-gray-200 dark:border-gray-700 shrink-0">
          {["upload", "processing", "preview", "complete"].map((s, i) => (
            <div key={s} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step === s
                    ? "bg-blue-600 text-white"
                    : ["upload", "processing", "preview", "complete"].indexOf(step) > i
                    ? "bg-green-600 text-white"
                    : "bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-400"
                }`}
              >
                {["upload", "processing", "preview", "complete"].indexOf(step) > i ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  i + 1
                )}
              </div>
              {i < 3 && (
                <div
                  className={`w-16 h-1 mx-2 ${
                    ["upload", "processing", "preview", "complete"].indexOf(step) > i
                      ? "bg-green-600"
                      : "bg-gray-200 dark:bg-gray-700"
                  }`}
                />
              )}
            </div>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Step 1: Upload */}
          {step === "upload" && (
            <div className="space-y-6">
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                Upload a bank statement to automatically detect recurring payments.
                We support PDF, CSV, OFX, QFX, and QIF formats.
              </p>

              {/* File Drop Zone */}
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  isDragging
                    ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                    : selectedFile
                    ? "border-green-500 bg-green-50 dark:bg-green-900/20"
                    : "border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.csv,.ofx,.qfx,.qif"
                  onChange={handleFileInput}
                  className="hidden"
                />

                {selectedFile ? (
                  <div className="flex flex-col items-center">
                    <svg
                      className="w-12 h-12 text-green-500 mb-3"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <p className="text-gray-900 dark:text-gray-100 font-medium">
                      {selectedFile.name}
                    </p>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">
                      {(selectedFile.size / 1024).toFixed(1)} KB
                    </p>
                    <button
                      onClick={() => {
                        setSelectedFile(null);
                        if (fileInputRef.current) fileInputRef.current.value = "";
                      }}
                      className="mt-2 text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      Choose different file
                    </button>
                  </div>
                ) : (
                  <div
                    onClick={() => fileInputRef.current?.click()}
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
                    <p className="text-gray-600 dark:text-gray-400">
                      Drop your statement here or{" "}
                      <span className="text-blue-600 dark:text-blue-400">browse</span>
                    </p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                      PDF, CSV, OFX, QFX, QIF
                    </p>
                  </div>
                )}
              </div>

              {/* Options */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Bank Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Bank (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="Search banks..."
                    value={bankSearch}
                    onChange={(e) => setBankSearch(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                  {bankSearch && filteredBanks.length > 0 && (
                    <div className="mt-1 max-h-40 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
                      {filteredBanks.slice(0, 5).map((bank) => (
                        <button
                          key={bank.id}
                          onClick={() => {
                            setSelectedBankId(bank.id);
                            setBankSearch(bank.name);
                          }}
                          className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center justify-between"
                        >
                          <span className="text-gray-900 dark:text-gray-100">{bank.name}</span>
                          <span className="text-gray-500 dark:text-gray-400 text-xs">
                            {bank.country_code}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    We&apos;ll auto-detect if not specified
                  </p>
                </div>

                {/* Currency */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Statement Currency
                  </label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="GBP">GBP (£)</option>
                    <option value="USD">USD ($)</option>
                    <option value="EUR">EUR (€)</option>
                    <option value="UAH">UAH (₴)</option>
                    <option value="CAD">CAD ($)</option>
                    <option value="AUD">AUD ($)</option>
                  </select>
                </div>
              </div>

              {/* AI Toggle */}
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={useAI}
                  onChange={(e) => setUseAI(e.target.checked)}
                  className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 dark:bg-gray-800"
                />
                <div>
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    Use AI for better detection
                  </span>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Improves accuracy but may take longer
                  </p>
                </div>
              </label>

              {/* Upload Button */}
              <button
                onClick={handleUpload}
                disabled={!selectedFile || isLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-3 px-4 rounded-lg transition-colors font-medium flex items-center justify-center space-x-2"
              >
                {uploadMutation.isPending ? (
                  <>
                    <svg
                      className="animate-spin w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    <span>Uploading...</span>
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                      />
                    </svg>
                    <span>Upload & Analyze</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Step 2: Processing */}
          {step === "processing" && (
            <div className="flex flex-col items-center justify-center py-12">
              <svg
                className="animate-spin w-16 h-16 text-blue-600 mb-4"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                Analyzing Your Statement
              </h3>
              <p className="text-gray-600 dark:text-gray-400 text-center max-w-sm">
                We&apos;re scanning your statement for recurring payments. This may take a moment...
              </p>
            </div>
          )}

          {/* Step 3: Preview */}
          {step === "preview" && preview && (
            <div className="space-y-6">
              {/* Summary */}
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {preview.summary.total_detected}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">Detected</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {preview.summary.selected_count}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">Selected</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                      {preview.summary.duplicate_count}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">Duplicates</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      {currency} {parseFloat(preview.summary.total_monthly_amount).toFixed(2)}
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">Monthly Total</p>
                  </div>
                </div>
              </div>

              {/* Bulk Actions */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => bulkUpdateMutation.mutate(true)}
                    className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    Select all
                  </button>
                  <span className="text-gray-400">|</span>
                  <button
                    onClick={() => bulkUpdateMutation.mutate(false)}
                    className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    Deselect all
                  </button>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {preview.detected_subscriptions.filter((s) => s.is_selected).length} of{" "}
                  {preview.detected_subscriptions.length} selected
                </p>
              </div>

              {/* Subscriptions List */}
              <div className="space-y-3 max-h-[40vh] overflow-y-auto">
                {preview.detected_subscriptions.map((sub) => (
                  <div
                    key={sub.id}
                    className={`border rounded-lg p-4 transition-colors ${
                      sub.status === "duplicate"
                        ? "border-yellow-300 bg-yellow-50 dark:border-yellow-700 dark:bg-yellow-900/20"
                        : sub.is_selected
                        ? "border-blue-300 bg-blue-50 dark:border-blue-700 dark:bg-blue-900/20"
                        : "border-gray-200 dark:border-gray-700"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Checkbox */}
                      <input
                        type="checkbox"
                        checked={sub.is_selected}
                        disabled={sub.status === "duplicate"}
                        onChange={() =>
                          toggleSelection.mutate({
                            id: sub.id,
                            isSelected: !sub.is_selected,
                          })
                        }
                        className="mt-1 rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 disabled:opacity-50"
                      />

                      {/* Details */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-gray-900 dark:text-gray-100 truncate">
                            {sub.name}
                          </h4>
                          {sub.status === "duplicate" && (
                            <span className="px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:text-yellow-400 rounded">
                              Duplicate
                            </span>
                          )}
                        </div>
                        <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {sub.currency} {parseFloat(sub.amount).toFixed(2)}
                          </span>
                          <span>·</span>
                          <span>{FREQUENCY_LABELS[sub.frequency] || sub.frequency}</span>
                          <span>·</span>
                          <span>{PAYMENT_TYPE_LABELS[sub.payment_type as PaymentType] || sub.payment_type}</span>
                        </div>
                        {sub.sample_descriptions && sub.sample_descriptions.length > 0 && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
                            e.g., &quot;{sub.sample_descriptions[0]}&quot;
                          </p>
                        )}
                      </div>

                      {/* Confidence */}
                      <div className="flex flex-col items-end">
                        <span
                          className={`px-2 py-0.5 text-xs font-medium rounded ${getConfidenceBadge(
                            sub.confidence
                          )}`}
                        >
                          {(sub.confidence * 100).toFixed(0)}%
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {sub.transaction_count} txns
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Import Options */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                {/* Card Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Assign to Card (Optional)
                  </label>
                  <select
                    value={selectedCardId}
                    onChange={(e) => setSelectedCardId(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  >
                    <option value="">No card</option>
                    {cards.map((card) => (
                      <option key={card.id} value={card.id}>
                        {card.name} ({card.bank_name})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Category Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Assign to Category (Optional)
                  </label>
                  <select
                    value={selectedCategoryId}
                    onChange={(e) => setSelectedCategoryId(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                  >
                    <option value="">No category</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id}>
                        {cat.icon} {cat.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-between pt-4">
                <button
                  onClick={() => setStep("upload")}
                  className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                >
                  ← Back
                </button>
                <button
                  onClick={() => confirmMutation.mutate()}
                  disabled={
                    confirmMutation.isPending ||
                    preview.detected_subscriptions.filter((s) => s.is_selected).length === 0
                  }
                  className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white py-2 px-6 rounded-lg transition-colors font-medium flex items-center space-x-2"
                >
                  {confirmMutation.isPending ? (
                    <>
                      <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                        />
                      </svg>
                      <span>Importing...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      <span>
                        Import {preview.detected_subscriptions.filter((s) => s.is_selected).length}{" "}
                        Subscriptions
                      </span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Complete */}
          {step === "complete" && importResult && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-4">
                <svg
                  className="w-10 h-10 text-green-600 dark:text-green-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Import Complete!
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6 text-center">
                Successfully imported {importResult.imported_count} recurring payment
                {importResult.imported_count !== 1 ? "s" : ""}.
              </p>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-6 mb-8">
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {importResult.imported_count}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Imported</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-500">
                    {importResult.skipped_count}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Skipped</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                    {importResult.duplicate_count}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Duplicates</p>
                </div>
              </div>

              <button
                onClick={handleClose}
                className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-8 rounded-lg transition-colors font-medium"
              >
                Done
              </button>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mt-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-3">
              <div className="flex items-start">
                <svg
                  className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 mr-2 shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
