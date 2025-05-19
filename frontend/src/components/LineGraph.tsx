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

interface GraphProps {
    data: {
        date: string;
        [key: string]: number | string;
    }[];
}

const colors = ["#10B981", "#3B82F6", "#FBBF24", "#EF4444"];

export const LineGraph = ({ data }: GraphProps) => {
    return (
        <ResponsiveContainer width="100%" height={200}>
            <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                {Object.keys(data[0])
                    .filter((key) => key !== "date")
                    .map((key, index) => (
                        <Line
                            key={key}
                            type="monotone"
                            dataKey={key}
                            stroke={colors[index % colors.length]}
                            activeDot={{ r: 6 }}
                        />
                    ))}
            </LineChart>
        </ResponsiveContainer>
    );
};
