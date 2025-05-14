import React from "react";

type Props = {
    children: React.ReactNode;
    className?: string;
};

export const Card = ({ children, className = "" }: Props) => {
    return (
        <div
            className={`rounded-2xl shadow-md p-4 bg-white dark:bg-slate-800 ${className}`}
        >
            {children}
        </div>
    );
};
