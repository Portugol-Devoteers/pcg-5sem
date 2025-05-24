import { useEffect, useState } from "react";
import { Card } from "../components/ui/card";
import { Company } from "../types/Company";
import { LineGraph } from "./LineGraph";
import axios from "axios";
import { Comparison } from "../types/Comparison";
import { GraphData } from "../types/GraphData";
import { Statistics } from "../types/Statistics";
import { STATISTICS_NAME } from "../types/Statistics";
import Loader from "./ui/loader";

interface Props {
    company: Company | null;
}

export const CompanyDetails = ({ company }: Props) => {
    const [graphData, setGraphData] = useState<GraphData | null>(null);

    const [comparisonData, setComparisonData] = useState<Comparison | null>(
        null
    );

    const [statistics, setStatistics] = useState<Statistics | null>(null);

    useEffect(() => {
        if (company) {
            setGraphData(null);
            setComparisonData(null);
            setStatistics(null);
            const fetchGraphData = async () => {
                const [graphRes] = await Promise.all([
                    axios.get(
                        `http://localhost:9000/prediction/${company.ticker}`
                    ),
                ]);
                setGraphData(graphRes.data);
            };
            const fetchStatistics = async () => {
                // const statisticsRes = await axios.get<Statistics>(
                //     `http://localhost:9000/statistics/${company.sector_id}`
                // );
                const [statisticsRes, comparisonRes] = await Promise.all([
                    axios.get<Statistics>(
                        `http://localhost:9000/statistics/${company.sector_id}`
                    ),
                    axios.get<Comparison>(
                        `http://localhost:9000/comparison/${company.ticker}`
                    ),
                ]);
                setStatistics(statisticsRes.data);
                setComparisonData(comparisonRes.data);
            };

            fetchGraphData();
            fetchStatistics();
        }
    }, [company]);

    if (!company) {
        return (
            <div className="flex items-center justify-center h-full text-sm text-muted">
                Selecione uma ação para ver os detalhes
            </div>
        );
    }

    if (!graphData) {
        return (
            <div className="flex items-center justify-center h-full text-sm text-muted">
                Carregando dados...
            </div>
        );
    }

    return (
        <div className="grid grid-cols-2 gap-4">
            {/* Card principal com gráfico e informações */}
            <Card className="p-4 col-span-2 relative">
                <div
                    className={`absolute top-4 right-4 h-10 w-32 bg-gradient-to-r ${
                        graphData.variation >= 0
                            ? "from-green-400 to-green-600"
                            : "from-red-400 to-red-600"
                    } rounded shadow-md`}
                />

                <h2 className="text-lg font-semibold">{company.ticker}</h2>
                <p className="text-sm text-muted">Setor: {company.sector}</p>
                <p
                    className={`text-2xl font-bold ${
                        graphData.variation >= 0
                            ? "text-green-400"
                            : "text-red-500"
                    }`}
                >
                    {graphData.price && `R$ ${graphData.price.toFixed(2)}`}
                </p>
                <p
                    className={`text-sm ${
                        graphData.variation >= 0
                            ? "text-green-400"
                            : "text-red-500"
                    }`}
                >
                    {graphData.variation >= 0
                        ? `+${graphData.variation.toFixed(2)}%`
                        : `${graphData.variation.toFixed(2)}%`}
                </p>

                <div className="mt-4">
                    <LineGraph data={graphData.graph} />
                </div>

                <div className="text-xs text-slate-400">
                    Atualizado em {graphData.updated_at}
                </div>
            </Card>

            {/* Comparação de modelos - Curto prazo */}
            <Card className="p-4">
                <strong className="block mb-2">📈 Curto Prazo (1 dia)</strong>
                {comparisonData ? (
                    <ul className="text-sm space-y-1">
                        {comparisonData.short_term.length > 0 && (
                            <li>
                                Real – R${" "}
                                {comparisonData.short_term[0].price_history_value.toFixed(
                                    2
                                )}
                            </li>
                        )}
                        {comparisonData.short_term.map((model, index) => (
                            <li key={index}>
                                {index + 1}º {model.model_name.toUpperCase()} –
                                R$ {model.value.toFixed(2)} –{" "}
                                {model.error_percent.toFixed(2)}% erro
                            </li>
                        ))}
                    </ul>
                ) : (
                    <Loader size="sm" />
                )}
            </Card>

            {/* Comparação de modelos - Longo prazo */}
            <Card className="p-4">
                <strong className="block mb-2">📉 Longo Prazo (7 dias)</strong>
                {comparisonData ? (
                    <ul className="text-sm space-y-1">
                        {comparisonData.long_term.length > 0 && (
                            <li>
                                Real – R${" "}
                                {comparisonData.long_term[0].price_history_value.toFixed(
                                    2
                                )}
                            </li>
                        )}
                        {comparisonData.long_term.map((model, index) => (
                            <li key={index}>
                                {index + 1}º {model.model_name.toUpperCase()} –
                                R$ {model.value.toFixed(2)} –{" "}
                                {model.error_percent.toFixed(2)}% erro
                            </li>
                        ))}
                    </ul>
                ) : (
                    <Loader size="sm" />
                )}
            </Card>

            {/* Estatísticas do Setor */}
            <Card className="p-4 col-span-2">
                <strong className="block mb-2">
                    📊 Estatísticas do Setor{" "}
                    {statistics && `(${statistics.sector.sector_name})`}
                </strong>
                {(statistics &&
                    Object.entries(statistics.sector.stats).map(
                        ([key, value]) => (
                            <li key={key}>
                                {
                                    STATISTICS_NAME[
                                        key as keyof Statistics["sector"]["stats"]
                                    ]
                                }
                                : {value.toFixed(2)}
                            </li>
                        )
                    )) || <Loader size="sm" />}
            </Card>

            {/* Estatísticas Gerais */}
            <Card className="p-4 col-span-2">
                <strong className="block mb-2">📊 Estatísticas Gerais</strong>
                {(statistics &&
                    Object.entries(statistics.general.stats).map(
                        ([key, value]) => (
                            <li key={key}>
                                {
                                    STATISTICS_NAME[
                                        key as keyof Statistics["general"]["stats"]
                                    ]
                                }
                                : {value.toFixed(2)}
                            </li>
                        )
                    )) || <Loader size="sm" />}
            </Card>
        </div>
    );
};
