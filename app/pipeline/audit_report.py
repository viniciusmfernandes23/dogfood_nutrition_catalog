import pandas as pd
import os
from datetime import datetime
from app.normalization.models import ValidationStatus

class AuditReporter:
    """
    Gera relatórios detalhados de auditoria do pipeline.
    """
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def generate_report(self, df: pd.DataFrame, fact_nutrient_df: pd.DataFrame):
        """
        Gera um relatório Markdown e CSV com as estatísticas de auditoria.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(self.output_dir, f"audit_report_{timestamp}.md")
        
        # 1. Estatísticas Gerais de Nutrientes
        total_collected = len(fact_nutrient_df)
        status_counts = fact_nutrient_df['status'].value_counts().to_dict()
        
        # 2. Produtos Reprovados (FAILED)
        failed_products = fact_nutrient_df[fact_nutrient_df['status'] == ValidationStatus.PRODUCT_MASS_BALANCE_FAILED]
        reproved_ids = failed_products['product_id'].unique()
        num_reproved = len(reproved_ids)
        
        # 3. Motivos de Reprovação/Revisão
        reasons = fact_nutrient_df[fact_nutrient_df['reason'].notna()]['reason'].value_counts().head(10).to_dict()

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# Relatório de Auditoria Automática do Pipeline\n\n")
            f.write(f"**Data da Execução**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            
            f.write("## 1. Resumo Executivo\n")
            f.write(f"- **Total de Nutrientes Coletados**: {total_collected}\n")
            f.write(f"- **Produtos com Falha Crítica (Reprovados)**: {num_reproved}\n\n")
            
            f.write("## 2. Distribuição por Status\n")
            f.write("| Status | Quantidade | Percentual |\n")
            f.write("| :--- | :--- | :--- |\n")
            for status, count in status_counts.items():
                pct = (count / total_collected) * 100
                f.write(f"| {status} | {count} | {pct:.2f}% |\n")
            f.write("\n")
            
            f.write("## 3. Principais Motivos de Auditoria/Falha\n")
            f.write("| Motivo | Ocorrências |\n")
            f.write("| :--- | :--- |\n")
            for reason, count in reasons.items():
                f.write(f"| {reason} | {count} |\n")
            f.write("\n")
            
            if num_reproved > 0:
                f.write("## 4. Amostra de Produtos Reprovados\n")
                f.write("| ID Produto | Motivo Principal |\n")
                f.write("| :--- | :--- |\n")
                sample_failed = failed_products[['product_id', 'reason']].drop_duplicates().head(20)
                for _, row in sample_failed.iterrows():
                    f.write(f"| {row['product_id']} | {row['reason']} |\n")
            
        print(f"Relatório de auditoria gerado em: {report_path}")
        return report_path
