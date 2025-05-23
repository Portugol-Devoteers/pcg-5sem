import { useEffect, useState } from "react";
import axios from "axios";
import { Header } from "../components/Header";
import { SectorSidebar } from "../components/SectorSidebar";
import { CompanyDetails } from "../components/CompanyDetails";
import { Company } from "../types/Company";

export default function B3Dashboard() {
    const [sectors, setSectors] = useState<string[]>([]);
    const [companies, setCompanies] = useState<Company[]>([]);
    const [selectedSector, setSelectedSector] = useState<string | null>(null);
    const [selectedCompany, setSelectedCompany] = useState<Company | null>(
        null
    );
    const [searchTerm, setSearchTerm] = useState("");
    const [filteredSuggestions, setFilteredSuggestions] = useState<Company[]>(
        []
    );

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [companyRes, sectorRes] = await Promise.all([
                    axios.get<Company[]>("http://localhost:9000/companies"),
                    axios.get<string[]>("http://localhost:9000/sectors"),
                ]);
                setCompanies(companyRes.data);
                setSectors(sectorRes.data);
            } catch (error) {
                console.error("Erro ao buscar dados da API:", error);
            }
        };

        fetchData();
    }, []);

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setSearchTerm(value);
        if (value.length > 0) {
            const valueLower = value.toLowerCase();
            const companyMatches = companies.filter(
                (c) =>
                    c.ticker.toLowerCase().includes(valueLower) ||
                    c.name.toLowerCase().includes(valueLower)
            );
            setFilteredSuggestions(companyMatches);
        } else {
            setFilteredSuggestions([]);
        }
    };

    const handleSelectSuggestion = (item: Company) => {
        setSelectedCompany(item);
        setSelectedSector(null);
        setSearchTerm(item.ticker);
        setFilteredSuggestions([]);
    };

    return (
        <div className="w-[1000px] h-[700px] overflow-hidden bg-white text-slate-900 rounded-2xl shadow-lg p-4 space-y-4 dark:bg-slate-700 dark:text-slate-200">
            <Header
                searchTerm={searchTerm}
                suggestions={filteredSuggestions}
                onChange={handleSearchChange}
                onSelect={handleSelectSuggestion}
            />

            <div className="flex h-[calc(100%-60px)] space-x-4 overflow-hidden">
                <SectorSidebar
                    sectors={sectors}
                    selectedSector={selectedSector}
                    selectedCompany={selectedCompany}
                    companies={companies}
                    onSelectSector={(sector) => {
                        setSelectedSector(sector);
                        setSelectedCompany(null);
                    }}
                    onSelectCompany={(company) => setSelectedCompany(company)}
                />

                <div className="flex-1 overflow-y-auto pb-4 pr-1">
                    <CompanyDetails company={selectedCompany} />
                </div>
            </div>
        </div>
    );
}
