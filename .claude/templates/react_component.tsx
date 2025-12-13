import React, { useState } from "react";

/**
 * Props for the [ComponentName] component.
 */
interface [ComponentName]Props {
  /**
   * [Description of prop]
   */
  title: string;

  /**
   * [Description of prop]
   */
  onAction?: () => void;

  /**
   * Additional CSS classes to apply.
   */
  className?: string;
}

/**
 * [ComponentName] - [Brief description of what this component does]
 *
 * [Longer description if needed]
 *
 * @example
 * ```tsx
 * <[ComponentName]
 *   title="Example Title"
 *   onAction={() => console.log("Action triggered")}
 * />
 * ```
 */
export function [ComponentName]({ title, onAction, className = "" }: [ComponentName]Props) {
  const [isActive, setIsActive] = useState(false);

  const handleClick = () => {
    setIsActive(!isActive);
    onAction?.();
  };

  return (
    <div className={`[component-name] ${className}`}>
      <h2 className="text-xl font-semibold">{title}</h2>
      <button
        onClick={handleClick}
        className={`mt-4 px-4 py-2 rounded-lg transition-colors ${
          isActive ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-800"
        }`}
      >
        {isActive ? "Active" : "Inactive"}
      </button>
    </div>
  );
}
