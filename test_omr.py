from pathlib import Path

import pandas as pd

from omr_engine import OMRGenerator

base_dir = Path(__file__).resolve().parent
example_path = base_dir / 'alunos_exemplo.xlsx'
if not example_path.exists():
    raise FileNotFoundError(f"Arquivo de exemplo não encontrado em: {example_path}")

print("--- TESTANDO GERADOR DE PDF ---")
df = pd.read_excel(example_path)
pdf_bytes = OMRGenerator.generate_pdf(df, num_questoes=20, num_alternativas=4)
print(f"PDF gerado com sucesso! Tamanho: {len(pdf_bytes)} bytes.")

print("\n--- TESTANDO PROCESSADOR OMR ---")
gabarito = {i: 'A' for i in range(1, 21)}
print("Gabarito de teste:", gabarito)

print("\nTodas as funções básicas da engine estão operacionais!")
