import { Card } from "../components/ui/card";
import { Company } from "../types/Company";
import { LineGraph } from "./LineGraph";

interface Props {
    company: Company | null;
}

export const CompanyDetails = ({ company }: Props) => {
    if (!company) {
        return (
            <div className="flex items-center justify-center h-full text-sm text-muted">
                Selecione uma ação para ver os detalhes
            </div>
        );
    }

    return (
        <div className="grid grid-cols-2 gap-4">
            {/* Card principal com gráfico e informações */}
            <Card className="p-4 col-span-2 relative">
                <div
                    className={`absolute top-4 right-4 h-10 w-32 bg-gradient-to-r ${
                        company.variation >= 0
                            ? "from-green-400 to-green-600"
                            : "from-red-400 to-red-600"
                    } rounded shadow-md`}
                />

                <h2 className="text-lg font-semibold">{company.ticker}</h2>
                <p className="text-sm text-muted">Setor: {company.sector}</p>
                <p
                    className={`text-2xl font-bold ${
                        company.variation >= 0
                            ? "text-green-400"
                            : "text-red-500"
                    }`}
                >
                    R$ {company.price.toFixed(2)}
                </p>
                <p
                    className={`text-sm ${
                        company.variation >= 0
                            ? "text-green-400"
                            : "text-red-500"
                    }`}
                >
                    {company.variation >= 0 ? "+" : ""}
                    {company.variation.toFixed(2)}%
                </p>

                <div className="mt-6 h-40">
                    <LineGraph
                        data={[
                            {
                                date: "01/10/2025",
                                XGBoost: 120,
                                GRU: 125,
                                LSTM: 130,
                                Real: 2,
                            },
                            {
                                date: "02/10/2025",
                                XGBoost: 122,
                                GRU: 127,
                                LSTM: 132,
                                Real: 122,
                            },
                            {
                                date: "03/10/2025",
                                XGBoost: 121,
                                GRU: 126,
                                LSTM: 131,
                                Real: 122,
                            },
                            {
                                date: "04/10/2025",
                                XGBoost: 123,
                                GRU: 128,
                                LSTM: 3,
                                Real: 122,
                            },
                            {
                                date: "05/10/2025",
                                XGBoost: 124,
                                GRU: 129,
                                LSTM: 50,
                                Real: 122,
                            },
                        ]}
                    />
                </div>

                <div className="pt-2 text-xs text-slate-400">
                    Atualizado em 14/05/2025
                </div>
            </Card>

            {/* Comparação de modelos - Curto prazo */}
            <Card className="p-4">
                <strong className="block mb-2">📈 Curto Prazo</strong>
                <ul className="text-sm space-y-1">
                    <li>Real – R$ 122,10</li>
                    <li>1º XGBoost – R$ 123,00 – 0.74% erro</li>
                    <li>2º GRU – R$ 121,40 – 0.57% erro</li>
                    <li>3º LSTM – R$ 124,00 – 1.55% erro</li>
                </ul>
            </Card>

            {/* Comparação de modelos - Longo prazo */}
            <Card className="p-4">
                <strong className="block mb-2">📉 Longo Prazo</strong>
                <ul className="text-sm space-y-1">
                    <li>Real – R$ 120,00</li>
                    <li>1º GRU – R$ 119,80 – 0.17% erro</li>
                    <li>2º XGBoost – R$ 121,50 – 1.25% erro</li>
                    <li>3º LSTM – R$ 123,00 – 2.50% erro</li>
                </ul>
            </Card>

            {/* Fundamentos da empresa (100% largura) */}
            <Card className="p-4 col-span-2">
                <strong className="block mb-2">
                    📊 Indicadores Fundamentais
                </strong>
                <ul className="text-sm space-y-1">
                    <li>Faturamento: R$ 210 bilhões</li>
                    <li>Lucro líquido: R$ 42 bilhões</li>
                    <li>ROE: 18%</li>
                    <li>Dívida líquida: R$ 90 bilhões</li>
                    <li>Patrimônio líquido: R$ 240 bilhões</li>
                    <li>Margem líquida: 20%</li>
                </ul>
            </Card>
        </div>
    );
};
