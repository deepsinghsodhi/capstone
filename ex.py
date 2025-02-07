import tabula
import pandas as pd

file_path = '/content/1-s2.0-S0308814617312839-Lentils.pdf'

tables = tabula.read_pdf(file_path, pages='all', multiple_tables=True)

writer = pd.ExcelWriter('exported_tables.xlsx', engine='openpyxl')

for i, table in enumerate(tables):
    table.to_excel(writer, sheet_name=f'Table_{i+1}', index=False)

writer.close()
