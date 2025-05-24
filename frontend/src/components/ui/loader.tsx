import React from "react";

interface LoaderProps {
    /** Tailwind size variant: 'sm', 'md' or 'lg' */
    size?: "sm" | "md" | "lg";
    /** Tailwind border-top color class, e.g., 'border-t-blue-500' */
    borderTopColorClass?: string;
}

const Loader: React.FC<LoaderProps> = ({
    size = "md",
    borderTopColorClass = "border-t-blue-500",
}) => {
    const sizeClasses: Record<string, string> = {
        sm: "w-6 h-6 border-2",
        md: "w-8 h-8 border-4",
        lg: "w-12 h-12 border-4",
    };

    return (
        <div
            className={`
        ${sizeClasses[size]} 
        border-gray-200 
        ${borderTopColorClass} 
        rounded-full 
        animate-spin
      `}
            role="status"
            aria-label="Loading"
        />
    );
};

export default Loader;
