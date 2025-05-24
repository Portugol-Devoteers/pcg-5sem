export interface Statistics {
    general: {
        stats: {
            Hit_rate_percentage: number;
            MAE: number;
            R2: number;
            RMSE: number;
            SMAPE_percentage: number;
            n_obs: number;
        };
    };
    sector: {
        sector_name: string;
        stats: {
            Hit_rate_percentage: number;
            MAE: number;
            R2: number;
            RMSE: number;
            SMAPE_percentage: number;
            n_obs: number;
        };
    };
}

export const STATISTICS_NAME = {
    MAE: "Erro Médio Absoluto (MAE)",
    RMSE: "Raiz do Erro Quadrático Médio (RMSE)",
    SMAPE_percentage: "Erro Percentual Absoluto Médio Simétrico (sMAPE)",
    R2: "Coeficiente de Determinação (R²)",
    Hit_rate_percentage: "Taxa de Acerto (%)",
    n_obs: "Número de Observações",
};
