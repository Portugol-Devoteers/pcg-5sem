import React from "react";

type Props = {
    placeholder?: string;
    className?: string;
    value?: string;
    onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
};

export const Input = ({
    placeholder,
    className = "",
    value,
    onChange,
}: Props) => {
    return (
        <input
            placeholder={placeholder}
            className={`w-full text-black dark:text-white placeholder:text-black placeholder:dark:text-white rounded-xl px-4 py-2 border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 ${className}`}
            value={value}
            onChange={(e) => {
                if (onChange) {
                    onChange(e);
                }
            }}
        />
    );
};
