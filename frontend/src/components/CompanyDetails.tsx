import { Card } from "../components/ui/card";
import { Company } from "../types/Company";

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
            <Card className="p-4 h-full">
                <h2 className="text-lg font-semibold">{company.ticker}</h2>
                <p className="text-sm text-muted">Setor: {company.sector}</p>
                <p className="text-2xl font-bold text-green-500">
                    R$ {company.price.toFixed(2)}
                </p>
                <p
                    className={`text-sm ${
                        company.variation >= 0
                            ? "text-green-400"
                            : "text-red-400"
                    }`}
                >
                    {company.variation >= 0 ? "+" : ""}
                    {company.variation.toFixed(2)}%
                </p>
                <div className="h-12 bg-gradient-to-r from-green-400 to-green-600 rounded mt-2" />
                <div className="pt-2 text-xs text-slate-400">
                    Atualizado em 14/05/2025
                </div>
            </Card>

            <Card className="p-4 h-full">
                <strong className="block mb-2">🧠 Análise Estatística</strong>
                <ul className="text-sm space-y-1">
                    <li>Média: R$ 36,10</li>
                    <li>Mediana: R$ 35,90</li>
                    <li>Desvio padrão: 2,14</li>
                </ul>
            </Card>

            <Card className="p-4 h-full">
                <strong className="block mb-2">📊 Fundamentos</strong>
                <ul className="text-sm space-y-1">
                    <li>Receita: R$ 210 bi</li>
                    <li>Lucro líquido: R$ 42 bi</li>
                    <li>ROE: 18%</li>
                </ul>
            </Card>

            <Card className="p-4 h-full">
                <strong className="block mb-2">📰 Notícias</strong>
                <ul className="text-sm list-disc list-inside space-y-1">
                    <li>{company.ticker} sobe após balanço positivo</li>
                    <li>Alta do setor impulsiona ações</li>
                </ul>
            </Card>
        </div>
    );
};
