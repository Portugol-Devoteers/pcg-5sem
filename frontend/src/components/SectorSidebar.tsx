import { Card } from "../components/ui/card";
import { Company } from "../types/Company";

interface Props {
    sectors: string[];
    selectedSector: string | null;
    selectedCompany: Company | null;
    companies: Company[];
    onSelectSector: (sector: string) => void;
    onSelectCompany: (company: Company) => void;
}

export const SectorSidebar = ({
    sectors,
    selectedSector,
    selectedCompany,
    companies,
    onSelectSector,
    onSelectCompany,
}: Props) => {
    const companiesToShow = selectedSector
        ? companies.filter((c) => c.sector === selectedSector)
        : [];

    return (
        <div className="w-[250px] space-y-4 overflow-y-auto pr-1">
            <Card className="p-4">
                <strong className="block mb-2">🎯 Setores</strong>
                <ul className="space-y-2 text-sm">
                    {sectors.map((sector) => (
                        <li key={sector}>
                            <button
                                className={`w-full text-left ${
                                    selectedSector === sector
                                        ? "font-bold text-blue-500"
                                        : "hover:text-blue-500"
                                }`}
                                onClick={() => onSelectSector(sector)}
                            >
                                {sector}
                            </button>
                        </li>
                    ))}
                </ul>
            </Card>

            {selectedSector && (
                <Card className="p-4">
                    <strong className="block mb-2">
                        📋 Ações de {selectedSector}
                    </strong>
                    <ul className="space-y-1 text-sm">
                        {companiesToShow.map((company) => (
                            <li key={company.ticker}>
                                <button
                                    className={`w-full text-left ${
                                        selectedCompany?.ticker ===
                                        company.ticker
                                            ? "font-bold text-green-500"
                                            : "hover:text-green-500"
                                    }`}
                                    onClick={() => onSelectCompany(company)}
                                >
                                    {company.ticker} - {company.name}
                                </button>
                            </li>
                        ))}
                    </ul>
                </Card>
            )}
        </div>
    );
};
