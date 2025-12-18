"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  categoriesApi,
  Category,
  CategoryCreate,
  CategoryUpdate,
  CategoryWithStats,
} from "@/lib/api";

// Common color presets
const COLOR_PRESETS = [
  "#EF4444", // red
  "#F97316", // orange
  "#F59E0B", // amber
  "#EAB308", // yellow
  "#84CC16", // lime
  "#22C55E", // green
  "#10B981", // emerald
  "#14B8A6", // teal
  "#06B6D4", // cyan
  "#0EA5E9", // sky
  "#3B82F6", // blue
  "#6366F1", // indigo
  "#8B5CF6", // violet
  "#A855F7", // purple
  "#D946EF", // fuchsia
  "#EC4899", // pink
];

// Common emoji icons
const ICON_PRESETS = [
  "🎬", "🎵", "📺", "🎮", "💻", "📱", "🏠", "🚗",
  "⚡", "💧", "🔥", "🌐", "📚", "💪", "🏥", "💼",
  "✈️", "🍔", "☕", "🛍️", "💳", "💰", "🎁", "📦",
];

interface EditModalProps {
  category: Category | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: CategoryCreate | CategoryUpdate) => void;
  isLoading: boolean;
}

function EditModal({ category, isOpen, onClose, onSave, isLoading }: EditModalProps) {
  const [name, setName] = useState(category?.name || "");
  const [description, setDescription] = useState(category?.description || "");
  const [color, setColor] = useState(category?.color || "#6366F1");
  const [icon, setIcon] = useState(category?.icon || "");
  const [budgetAmount, setBudgetAmount] = useState(
    category?.budget_amount ? parseFloat(category.budget_amount) : 0
  );
  const [hasBudget, setHasBudget] = useState(!!category?.budget_amount);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data: CategoryCreate | CategoryUpdate = {
      name: name.trim(),
      description: description.trim() || undefined,
      color,
      icon: icon || undefined,
      budget_amount: hasBudget && budgetAmount > 0 ? budgetAmount : undefined,
    };
    onSave(data);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-800">
        <h2 className="mb-4 text-xl font-semibold text-gray-800 dark:text-gray-100">
          {category ? "Edit Category" : "New Category"}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Name */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input-glass w-full"
              placeholder="Category name"
              required
              disabled={category?.is_system}
            />
          </div>

          {/* Description */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input-glass w-full resize-none"
              rows={2}
              placeholder="Optional description"
              disabled={category?.is_system}
            />
          </div>

          {/* Color */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Color
            </label>
            <div className="flex flex-wrap gap-2">
              {COLOR_PRESETS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setColor(c)}
                  className={`h-8 w-8 rounded-full transition-transform hover:scale-110 ${
                    color === c ? "ring-2 ring-offset-2 ring-blue-500" : ""
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
            <div className="mt-2 flex items-center gap-2">
              <input
                type="color"
                value={color}
                onChange={(e) => setColor(e.target.value)}
                className="h-8 w-8 cursor-pointer rounded border-0"
              />
              <input
                type="text"
                value={color}
                onChange={(e) => setColor(e.target.value)}
                className="input-glass flex-1 font-mono text-sm"
                pattern="^#[0-9A-Fa-f]{6}$"
              />
            </div>
          </div>

          {/* Icon */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Icon
            </label>
            <div className="flex flex-wrap gap-2">
              {ICON_PRESETS.map((i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setIcon(i)}
                  className={`h-8 w-8 rounded-lg text-lg transition-transform hover:scale-110 ${
                    icon === i
                      ? "bg-blue-100 ring-2 ring-blue-500 dark:bg-blue-900"
                      : "bg-gray-100 dark:bg-slate-700"
                  }`}
                >
                  {i}
                </button>
              ))}
            </div>
            <input
              type="text"
              value={icon}
              onChange={(e) => setIcon(e.target.value)}
              className="input-glass mt-2 w-full"
              placeholder="Custom emoji or icon name"
              maxLength={10}
            />
          </div>

          {/* Budget */}
          <div>
            <label className="mb-2 flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              <input
                type="checkbox"
                checked={hasBudget}
                onChange={(e) => setHasBudget(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300"
                disabled={category?.is_system}
              />
              Set monthly budget
            </label>
            {hasBudget && (
              <div className="flex items-center gap-2">
                <span className="text-gray-500">£</span>
                <input
                  type="number"
                  value={budgetAmount}
                  onChange={(e) => setBudgetAmount(parseFloat(e.target.value) || 0)}
                  className="input-glass flex-1"
                  min={0}
                  step={0.01}
                  placeholder="0.00"
                />
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn-glass px-4 py-2"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-lg bg-blue-500 px-4 py-2 font-medium text-white hover:bg-blue-600 disabled:opacity-50"
              disabled={isLoading || !name.trim()}
            >
              {isLoading ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

interface CategoryCardProps {
  category: CategoryWithStats;
  onEdit: () => void;
  onDelete: () => void;
}

function CategoryCard({ category, onEdit, onDelete }: CategoryCardProps) {
  const budgetPercent = category.budget_used_percentage;

  return (
    <div className="glass-card group relative overflow-hidden rounded-xl p-4">
      {/* Color bar */}
      <div
        className="absolute left-0 top-0 h-full w-1"
        style={{ backgroundColor: category.color }}
      />

      <div className="flex items-start gap-3">
        {/* Icon */}
        <div
          className="flex h-10 w-10 items-center justify-center rounded-lg text-xl"
          style={{ backgroundColor: category.color + "20" }}
        >
          {category.icon || "📁"}
        </div>

        {/* Content */}
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-800 dark:text-gray-100">
              {category.name}
            </h3>
            {category.is_system && (
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500 dark:bg-slate-700 dark:text-gray-400">
                System
              </span>
            )}
          </div>
          {category.description && (
            <p className="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
              {category.description}
            </p>
          )}

          {/* Stats */}
          <div className="mt-2 flex flex-wrap gap-4 text-sm">
            <span className="text-gray-600 dark:text-gray-300">
              {category.subscription_count} subscription
              {category.subscription_count !== 1 && "s"}
            </span>
            <span className="font-medium text-gray-800 dark:text-gray-100">
              £{parseFloat(category.total_monthly).toFixed(2)}/mo
            </span>
          </div>

          {/* Budget progress */}
          {category.budget_amount && budgetPercent !== null && (
            <div className="mt-3">
              <div className="mb-1 flex justify-between text-xs">
                <span className="text-gray-500">
                  Budget: £{parseFloat(category.budget_amount).toFixed(0)}
                </span>
                <span
                  className={
                    category.is_over_budget
                      ? "font-medium text-red-500"
                      : "text-gray-500"
                  }
                >
                  {budgetPercent.toFixed(0)}%
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-gray-200 dark:bg-slate-700">
                <div
                  className={`h-full transition-all ${
                    category.is_over_budget
                      ? "bg-red-500"
                      : budgetPercent > 80
                        ? "bg-yellow-500"
                        : "bg-green-500"
                  }`}
                  style={{ width: `${Math.min(budgetPercent, 100)}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          <button
            onClick={onEdit}
            className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:hover:bg-slate-700"
            title="Edit"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
              />
            </svg>
          </button>
          {!category.is_system && (
            <button
              onClick={onDelete}
              className="rounded-lg p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
              title="Delete"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CategoriesSettings() {
  const queryClient = useQueryClient();
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  // Fetch categories with stats
  const {
    data: categories,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["categories", "with-stats"],
    queryFn: () => categoriesApi.getWithStats("GBP", true),
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      setIsModalOpen(false);
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: CategoryUpdate }) =>
      categoriesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      setIsModalOpen(false);
      setEditingCategory(null);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: categoriesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      setDeleteConfirm(null);
    },
  });

  // Create defaults mutation
  const createDefaultsMutation = useMutation({
    mutationFn: categoriesApi.createDefaults,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] });
    },
  });

  const handleSave = (data: CategoryCreate | CategoryUpdate) => {
    if (editingCategory) {
      updateMutation.mutate({ id: editingCategory.id, data });
    } else {
      createMutation.mutate(data as CategoryCreate);
    }
  };

  const handleEdit = (category: CategoryWithStats) => {
    setEditingCategory(category);
    setIsModalOpen(true);
  };

  const handleNew = () => {
    setEditingCategory(null);
    setIsModalOpen(true);
  };

  const handleDelete = (id: string) => {
    setDeleteConfirm(id);
  };

  const confirmDelete = () => {
    if (deleteConfirm) {
      deleteMutation.mutate(deleteConfirm);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between">
          <div className="h-8 w-48 animate-pulse rounded-lg bg-gray-200 dark:bg-slate-700" />
          <div className="h-10 w-32 animate-pulse rounded-lg bg-gray-200 dark:bg-slate-700" />
        </div>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-32 animate-pulse rounded-xl bg-gray-200 dark:bg-slate-700"
          />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl bg-red-50 p-4 text-red-600 dark:bg-red-900/20 dark:text-red-400">
        Failed to load categories. Please try again.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
            Categories
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Organize your subscriptions with custom categories
          </p>
        </div>
        <div className="flex gap-2">
          {categories?.length === 0 && (
            <button
              onClick={() => createDefaultsMutation.mutate()}
              className="btn-glass px-4 py-2 text-sm"
              disabled={createDefaultsMutation.isPending}
            >
              {createDefaultsMutation.isPending
                ? "Creating..."
                : "Create Defaults"}
            </button>
          )}
          <button
            onClick={handleNew}
            className="flex items-center gap-2 rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            New Category
          </button>
        </div>
      </div>

      {/* Categories list */}
      {categories && categories.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {categories.map((category) => (
            <CategoryCard
              key={category.id}
              category={category}
              onEdit={() => handleEdit(category)}
              onDelete={() => handleDelete(category.id)}
            />
          ))}
        </div>
      ) : (
        <div className="rounded-xl border-2 border-dashed border-gray-200 p-8 text-center dark:border-slate-700">
          <div className="text-4xl">📁</div>
          <h3 className="mt-2 font-medium text-gray-800 dark:text-gray-100">
            No categories yet
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Create categories to organize your subscriptions
          </p>
          <button
            onClick={() => createDefaultsMutation.mutate()}
            className="mt-4 rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white hover:bg-blue-600"
            disabled={createDefaultsMutation.isPending}
          >
            {createDefaultsMutation.isPending
              ? "Creating..."
              : "Create Default Categories"}
          </button>
        </div>
      )}

      {/* Edit Modal */}
      <EditModal
        category={editingCategory}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingCategory(null);
        }}
        onSave={handleSave}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />

      {/* Delete Confirmation */}
      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-800">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
              Delete Category?
            </h3>
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              This will remove the category. Subscriptions in this category will
              be uncategorized.
            </p>
            <div className="mt-4 flex justify-end gap-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="btn-glass px-4 py-2"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                className="rounded-lg bg-red-500 px-4 py-2 font-medium text-white hover:bg-red-600"
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
