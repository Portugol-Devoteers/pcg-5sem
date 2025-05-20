import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";
import { useMemo, useState } from "react";

interface GraphProps {
    data: {
        date: string;
        [key: string]: number | string;
    }[];
}

const colors = {
    real: "#10B981", // verde
    lstm: "#3B82F6", // azul
    gru: "#FBBF24", // amarelo
    xgboost: "#EF4444", // vermelho
};

const modelKeys = ["real", "lstm", "gru", "xgboost"];

export const LineGraph = ({ data }: GraphProps) => {
    const [activeModels, setActiveModels] = useState<string[]>(modelKeys);

    const toggleModel = (model: string) => {
        setActiveModels((prev) =>
            prev.includes(model)
                ? prev.filter((m) => m !== model)
                : [...prev, model]
        );
    };

    // Cálculo automático do eixo Y
    const [yMin, yMax] = useMemo(() => {
        let allValues: number[] = [];

        data.forEach((item) => {
            Object.entries(item).forEach(([key, value]) => {
                if (
                    key !== "date" &&
                    activeModels.includes(key) &&
                    typeof value === "number"
                ) {
                    allValues.push(value);
                }
            });
        });

        if (allValues.length === 0) return [0, 100];

        const min = Math.min(...allValues);
        const max = Math.max(...allValues);

        return [Math.floor(min - 0.5), Math.ceil(max + 0.5)];
    }, [data, activeModels]);

    return (
        <div className="w-full flex flex-col gap-2">
            <div className="flex flex-wrap gap-4 justify-center">
                {modelKeys.map((model) => (
                    <label
                        key={model}
                        className="flex items-center gap-1 text-sm"
                    >
                        <input
                            type="checkbox"
                            checked={activeModels.includes(model)}
                            onChange={() => toggleModel(model)}
                            className="accent-blue-500"
                        />
                        <span className="capitalize">{model}</span>
                    </label>
                ))}
            </div>

            <div className="w-full">
                <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis domain={[yMin, yMax]} />
                        <Tooltip />
                        <Legend />
                        {data.length > 0 &&
                            Object.keys(data[0])
                                .filter(
                                    (key) =>
                                        key !== "date" &&
                                        activeModels.includes(key)
                                )
                                .map((key) => (
                                    <Line
                                        key={key}
                                        type="monotone"
                                        dataKey={key}
                                        stroke={
                                            colors[key as keyof typeof colors]
                                        }
                                        activeDot={{ r: 6 }}
                                    />
                                ))}
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};
