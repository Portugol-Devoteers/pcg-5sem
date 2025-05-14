import React from "react";
import classNames from "classnames";

type Props = {
    children: React.ReactNode;
    onClick?: () => void;
    variant?: "default" | "outline" | "ghost";
    size?: "sm" | "md";
};

export const Button = ({
    children,
    onClick,
    variant = "default",
    size = "md",
}: Props) => {
    const base = "rounded-xl font-medium transition-all duration-200";

    const variants = {
        default: "bg-blue-500 text-white hover:bg-blue-600",
        outline: "border border-blue-500 text-blue-500 hover:bg-blue-50",
        ghost: "text-blue-500 hover:bg-blue-100",
    };

    const sizes = {
        sm: "text-sm px-3 py-1",
        md: "text-base px-4 py-2",
    };

    return (
        <button
            className={classNames(base, variants[variant], sizes[size])}
            onClick={onClick}
        >
            {children}
        </button>
    );
};
