import { Input } from "../components/ui/input";
import { Company } from "../types/Company";

interface HeaderProps {
    searchTerm: string;
    suggestions: Company[];
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onSelect: (company: Company) => void;
}

export const Header = ({
    searchTerm,
    suggestions,
    onChange,
    onSelect,
}: HeaderProps) => (
    <div className="relative flex items-center justify-between">
        <h1 className="text-xl font-bold tracking-tight">SmartB3</h1>
        <div className="relative w-1/2">
            <Input
                placeholder="Buscar ação (ex: PETR4)"
                value={searchTerm}
                onChange={onChange}
                className="w-full"
            />
            {suggestions.length > 0 && (
                <ul className="absolute z-10 w-full bg-white border border-slate-300 rounded shadow mt-1 text-sm max-h-60 overflow-y-auto pr-1">
                    {suggestions.map((item, index) => (
                        <li
                            key={`${item.ticker}-${index}`}
                            className="px-4 py-2 hover:bg-slate-100 cursor-pointer"
                            onClick={() => onSelect(item)}
                        >
                            {item.ticker} - {item.name}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    </div>
);
