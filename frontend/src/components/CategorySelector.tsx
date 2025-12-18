"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, FolderOpen, Check } from "lucide-react";
import { categoriesApi, type Category } from "@/lib/api";
import { cn } from "@/lib/utils";

interface CategorySelectorProps {
  value: string | null;
  onChange: (categoryId: string | null, categoryName?: string) => void;
  disabled?: boolean;
  className?: string;
}

export function CategorySelector({
  value,
  onChange,
  disabled = false,
  className,
}: CategorySelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Fetch categories
  const { data: categories = [], isLoading } = useQuery({
    queryKey: ["categories"],
    queryFn: () => categoriesApi.getAll(),
  });

  // Find selected category
  const selectedCategory = categories.find((cat) => cat.id === value);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (category: Category | null) => {
    if (category) {
      onChange(category.id, category.name);
    } else {
      onChange(null, undefined);
    }
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          "w-full flex items-center justify-between gap-2 px-4 py-3 rounded-xl border-2 transition-all duration-200",
          "text-left text-gray-900 dark:text-gray-100",
          isOpen
            ? "border-blue-400 dark:border-blue-500 ring-2 ring-blue-100 dark:ring-blue-900/50"
            : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600",
          disabled && "opacity-50 cursor-not-allowed bg-gray-100 dark:bg-gray-800",
          "bg-white/50 dark:bg-gray-800/50"
        )}
      >
        <div className="flex items-center gap-3">
          {selectedCategory ? (
            <>
              <div
                className="w-6 h-6 rounded-lg flex items-center justify-center text-sm"
                style={{ backgroundColor: `${selectedCategory.color}20` }}
              >
                {selectedCategory.icon || (
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: selectedCategory.color }}
                  />
                )}
              </div>
              <span className="font-medium">{selectedCategory.name}</span>
            </>
          ) : (
            <>
              <FolderOpen className="w-5 h-5 text-gray-400" />
              <span className="text-gray-500 dark:text-gray-400">Select category</span>
            </>
          )}
        </div>
        <ChevronDown
          className={cn(
            "w-5 h-5 text-gray-400 transition-transform duration-200",
            isOpen && "rotate-180"
          )}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute z-50 w-full mt-2 py-2 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-xl max-h-64 overflow-y-auto"
          >
            {isLoading ? (
              <div className="px-4 py-3 text-center text-gray-500 dark:text-gray-400">
                Loading categories...
              </div>
            ) : categories.length === 0 ? (
              <div className="px-4 py-3 text-center text-gray-500 dark:text-gray-400">
                <p className="mb-2">No categories yet</p>
                <p className="text-xs">Create categories in Settings</p>
              </div>
            ) : (
              <>
                {/* No category option */}
                <button
                  type="button"
                  onClick={() => handleSelect(null)}
                  className={cn(
                    "w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors",
                    !value
                      ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                      : "hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
                  )}
                >
                  <FolderOpen className="w-5 h-5 text-gray-400" />
                  <span>No category</span>
                  {!value && <Check className="w-4 h-4 ml-auto text-blue-500" />}
                </button>

                <div className="h-px bg-gray-100 dark:bg-gray-800 my-1" />

                {/* Category options */}
                {categories.map((category) => (
                  <button
                    key={category.id}
                    type="button"
                    onClick={() => handleSelect(category)}
                    className={cn(
                      "w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors",
                      value === category.id
                        ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                        : "hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
                    )}
                  >
                    <div
                      className="w-6 h-6 rounded-lg flex items-center justify-center text-sm"
                      style={{ backgroundColor: `${category.color}20` }}
                    >
                      {category.icon || (
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: category.color }}
                        />
                      )}
                    </div>
                    <span className="flex-1">{category.name}</span>
                    {category.budget_amount && (
                      <span className="text-xs text-gray-400">
                        £{Number(category.budget_amount).toFixed(0)}/mo
                      </span>
                    )}
                    {value === category.id && (
                      <Check className="w-4 h-4 text-blue-500" />
                    )}
                  </button>
                ))}
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
