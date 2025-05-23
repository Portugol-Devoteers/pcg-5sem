export interface GraphData {
    variation: number;
    price: number;
    updated_at: string;
    graph: {
        date: string;
        [key: string]: number | string;
    }[];
}
