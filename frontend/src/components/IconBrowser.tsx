"use client";

import { useState, useMemo, useCallback } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  iconApi,
  type Icon,
  type IconStyle,
} from "@/lib/api";
import {
  X,
  Search,
  Sparkles,
  Check,
  RefreshCw,
  AlertCircle,
  Palette,
  Wand2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "@/components/Toast";

interface IconBrowserProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (icon: Icon) => void;
  serviceName?: string;
}

const ICON_STYLES: { value: IconStyle; label: string; description: string }[] = [
  { value: "minimal", label: "Minimal", description: "Clean, flat design" },
  { value: "branded", label: "Branded", description: "Modern, professional" },
  { value: "playful", label: "Playful", description: "Fun, colorful" },
  { value: "corporate", label: "Corporate", description: "Serious, business" },
];

const POPULAR_SERVICES = [
  "netflix", "spotify", "youtube", "github", "figma", "slack",
  "notion", "discord", "adobe", "microsoft", "google", "amazon",
];

// Single icon card component
function IconCard({
  icon,
  isSelected,
  onClick,
}: {
  icon: Icon;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      whileHover={{ scale: 1.05, y: -2 }}
      whileTap={{ scale: 0.95 }}
      className={cn(
        "relative flex flex-col items-center gap-2 p-4 rounded-2xl transition-all duration-200",
        isSelected
          ? "bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/30 dark:to-indigo-900/30 border-2 border-blue-400 dark:border-blue-500 shadow-lg"
          : "glass-card-subtle hover:shadow-md"
      )}
    >
      {/* Icon image */}
      <div
        className="w-14 h-14 rounded-xl flex items-center justify-center shadow-sm"
        style={{ backgroundColor: icon.brand_color ? `${icon.brand_color}15` : "rgba(0,0,0,0.05)" }}
      >
        {icon.icon_url ? (
          <img
            src={icon.icon_url}
            alt={icon.display_name || icon.service_name}
            className="w-8 h-8"
            style={{
              filter: icon.brand_color
                ? `drop-shadow(0 1px 2px ${icon.brand_color}40)`
                : undefined,
            }}
          />
        ) : (
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-lg"
            style={{
              background: icon.brand_color
                ? `linear-gradient(135deg, ${icon.brand_color} 0%, ${icon.brand_color}cc 100%)`
                : "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)",
            }}
          >
            {(icon.display_name || icon.service_name).charAt(0).toUpperCase()}
          </div>
        )}
      </div>

      {/* Service name */}
      <span className="text-xs font-medium text-gray-700 dark:text-gray-300 text-center line-clamp-1">
        {icon.display_name || icon.service_name}
      </span>

      {/* Source badge */}
      <div className="absolute top-1 right-1">
        {icon.source === "ai_generated" && (
          <div className="w-5 h-5 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
            <Sparkles className="w-3 h-3 text-white" />
          </div>
        )}
        {icon.is_verified && (
          <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center">
            <Check className="w-3 h-3 text-white" />
          </div>
        )}
      </div>

      {/* Selection indicator */}
      {isSelected && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 flex items-center justify-center shadow-lg"
        >
          <Check className="w-4 h-4 text-white" />
        </motion.div>
      )}
    </motion.button>
  );
}

// Quick service picker
function QuickServicePicker({
  onSelect,
}: {
  onSelect: (serviceName: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {POPULAR_SERVICES.map((name) => (
        <motion.button
          key={name}
          type="button"
          onClick={() => onSelect(name)}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="px-3 py-1.5 rounded-lg text-xs font-medium glass-card-subtle hover:shadow-md transition-all"
        >
          {name.charAt(0).toUpperCase() + name.slice(1)}
        </motion.button>
      ))}
    </div>
  );
}

export function IconBrowser({
  isOpen,
  onClose,
  onSelect,
  serviceName = "",
}: IconBrowserProps) {
  const [searchQuery, setSearchQuery] = useState(serviceName);
  const [selectedIcon, setSelectedIcon] = useState<Icon | null>(null);
  const [generateStyle, setGenerateStyle] = useState<IconStyle>("branded");
  const [generateColor, setGenerateColor] = useState("#6366f1");

  // Search for icons
  const { data: searchResults, isLoading: isSearching } = useQuery({
    queryKey: ["icon-search", searchQuery],
    queryFn: () => iconApi.search({ query: searchQuery, include_ai: true }),
    enabled: searchQuery.length >= 2,
    staleTime: 30 * 1000, // 30 seconds
  });

  // Fetch single icon
  const { data: fetchedIcon, isLoading: isFetching } = useQuery({
    queryKey: ["icon-fetch", searchQuery],
    queryFn: () => iconApi.getIcon(searchQuery),
    enabled: searchQuery.length >= 2 && (!searchResults || searchResults.total === 0),
    staleTime: 60 * 1000, // 1 minute
  });

  // Generate icon mutation
  const generateMutation = useMutation({
    mutationFn: () =>
      iconApi.generate({
        service_name: searchQuery,
        style: generateStyle,
        brand_color: generateColor,
      }),
    onSuccess: (icon) => {
      if (icon) {
        setSelectedIcon(icon);
        toast.success("Icon generated", `AI generated icon for ${searchQuery}`);
      } else {
        toast.error("Generation failed", "Could not generate icon. Please try again.");
      }
    },
    onError: () => {
      toast.error("Generation failed", "Could not generate icon. Please try again.");
    },
  });

  // Combine search results with fetched icon
  const icons = useMemo(() => {
    const results: Icon[] = [];

    if (searchResults?.icons) {
      results.push(...searchResults.icons);
    }

    if (fetchedIcon && !results.some((i) => i.id === fetchedIcon.id)) {
      results.unshift(fetchedIcon);
    }

    return results;
  }, [searchResults, fetchedIcon]);

  const handleSelect = useCallback(
    (icon: Icon) => {
      setSelectedIcon(icon);
    },
    []
  );

  const handleConfirm = useCallback(() => {
    if (selectedIcon) {
      onSelect(selectedIcon);
      onClose();
    }
  }, [selectedIcon, onSelect, onClose]);

  const handleQuickSelect = useCallback((name: string) => {
    setSearchQuery(name);
  }, []);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 z-50"
        role="dialog"
        aria-modal="true"
        aria-labelledby="icon-browser-title"
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          onClick={(e) => e.stopPropagation()}
          className="glass-card rounded-3xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden relative"
        >
          {/* Decorative gradients */}
          <div className="absolute -top-20 -right-20 w-40 h-40 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full opacity-20 blur-3xl" />
          <div className="absolute -bottom-20 -left-20 w-40 h-40 bg-gradient-to-br from-pink-400 to-orange-500 rounded-full opacity-20 blur-3xl" />

          {/* Header */}
          <div className="relative p-6 border-b border-gray-200 dark:border-gray-700">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <motion.div
                  whileHover={{ scale: 1.1, rotate: 10 }}
                  className="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center shadow-lg"
                >
                  <Palette className="w-6 h-6 text-white" />
                </motion.div>
                <div>
                  <h2
                    id="icon-browser-title"
                    className="text-2xl font-bold text-gray-900 dark:text-gray-100"
                  >
                    Icon Browser
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Search or generate icons for your services
                  </p>
                </div>
              </div>
              <motion.button
                onClick={onClose}
                whileHover={{ scale: 1.1, rotate: 90 }}
                whileTap={{ scale: 0.9 }}
                className="p-2 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                aria-label="Close icon browser"
              >
                <X className="w-6 h-6 text-gray-400" />
              </motion.button>
            </div>

            {/* Search input */}
            <div className="relative mt-4">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for a service..."
                className="w-full pl-12 pr-4 py-3 rounded-xl border-2 border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:ring-0 focus:border-blue-400 dark:focus:border-blue-500 transition-all"
                autoFocus
              />
              {(isSearching || isFetching) && (
                <RefreshCw className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 animate-spin" />
              )}
            </div>

            {/* Quick picks */}
            <div className="mt-3">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                Popular services
              </p>
              <QuickServicePicker onSelect={handleQuickSelect} />
            </div>
          </div>

          {/* Content */}
          <div className="relative flex-1 overflow-y-auto p-6">
            {/* Icon grid */}
            {icons.length > 0 ? (
              <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-3">
                {icons.map((icon) => (
                  <IconCard
                    key={icon.id}
                    icon={icon}
                    isSelected={selectedIcon?.id === icon.id}
                    onClick={() => handleSelect(icon)}
                  />
                ))}
              </div>
            ) : searchQuery.length >= 2 && !isSearching && !isFetching ? (
              <div className="flex flex-col items-center justify-center py-12">
                <AlertCircle className="w-12 h-12 text-gray-300 dark:text-gray-600 mb-4" />
                <p className="text-gray-500 dark:text-gray-400 text-center mb-6">
                  No icons found for "{searchQuery}"
                </p>

                {/* AI generation option */}
                <div className="w-full max-w-sm space-y-4 p-4 rounded-2xl bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border-2 border-purple-200 dark:border-purple-700">
                  <div className="flex items-center gap-2 text-purple-700 dark:text-purple-300">
                    <Wand2 className="w-5 h-5" />
                    <span className="font-semibold">Generate with AI</span>
                  </div>

                  {/* Style selector */}
                  <div className="space-y-2">
                    <label className="text-xs font-medium text-gray-600 dark:text-gray-400">
                      Style
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {ICON_STYLES.map((style) => (
                        <button
                          key={style.value}
                          type="button"
                          onClick={() => setGenerateStyle(style.value)}
                          className={cn(
                            "px-3 py-2 rounded-lg text-xs font-medium transition-all",
                            generateStyle === style.value
                              ? "bg-purple-500 text-white"
                              : "bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-purple-100 dark:hover:bg-purple-900/30"
                          )}
                        >
                          {style.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Color picker */}
                  <div className="space-y-2">
                    <label className="text-xs font-medium text-gray-600 dark:text-gray-400">
                      Brand Color
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        type="color"
                        value={generateColor}
                        onChange={(e) => setGenerateColor(e.target.value)}
                        className="w-10 h-10 rounded-lg cursor-pointer border-2 border-gray-200 dark:border-gray-700"
                      />
                      <input
                        type="text"
                        value={generateColor}
                        onChange={(e) => setGenerateColor(e.target.value)}
                        className="flex-1 px-3 py-2 rounded-lg border-2 border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm font-mono"
                        placeholder="#6366f1"
                      />
                    </div>
                  </div>

                  {/* Generate button */}
                  <motion.button
                    onClick={() => generateMutation.mutate()}
                    disabled={generateMutation.isPending}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className={cn(
                      "w-full py-3 rounded-xl font-semibold text-white shadow-lg transition-all",
                      "bg-gradient-to-r from-purple-500 to-pink-500 hover:shadow-xl",
                      generateMutation.isPending && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    {generateMutation.isPending ? (
                      <span className="flex items-center justify-center gap-2">
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        Generating...
                      </span>
                    ) : (
                      <span className="flex items-center justify-center gap-2">
                        <Sparkles className="w-4 h-4" />
                        Generate Icon
                      </span>
                    )}
                  </motion.button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-gray-400 dark:text-gray-500">
                <Search className="w-12 h-12 mb-4" />
                <p>Enter a service name to search for icons</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="relative p-6 border-t border-gray-200 dark:border-gray-700 flex gap-3">
            <motion.button
              type="button"
              onClick={onClose}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex-1 px-6 py-3 rounded-xl border-2 border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              Cancel
            </motion.button>
            <motion.button
              type="button"
              onClick={handleConfirm}
              disabled={!selectedIcon}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              className={cn(
                "flex-1 px-6 py-3 rounded-xl font-semibold text-white shadow-lg transition-all",
                selectedIcon
                  ? "bg-gradient-to-r from-blue-500 to-indigo-600 hover:shadow-xl"
                  : "bg-gray-300 dark:bg-gray-700 cursor-not-allowed"
              )}
            >
              Select Icon
            </motion.button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
