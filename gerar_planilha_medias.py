"""Adiciona a aba 'means of 4 positions' a Capturas_tomate_NIRS_11agosto (1).xlsx
com o espectro medio das 4 orientacoes (O1, O2, O3, O4) para cada fruto.

- Linhas: 4200 comprimentos de onda (400-2500 nm, passo 0,5 nm)
- Colunas: 'Wavelength (nm)' + 21 frutos (TIR1..TIR7, THR1..THR7, TSR1..TSR7)
- Cada valor = media(O1, O2, O3, O4) daquele fruto naquele comprimento de onda
"""
import openpyxl

ARQ = 'Capturas_tomate_NIRS_11agosto (1).xlsx'
ABAS_O = ['O1 (stem-end view)', 'O2 (blossom-end view)',
          'O3 (stem-end to the right)', 'O4 (stem-end to the left)']
NOVA_ABA = 'means of 4 positions'

wb = openpyxl.load_workbook(ARQ)

# --- Ler as 4 abas de orientacao (coluna 1 = wavelength; colunas 2..22 = 21 frutos) ---
dados = {}          # aba -> lista de linhas (tuplas)
for aba in ABAS_O:
    ws = wb[aba]
    dados[aba] = [list(r) for r in ws.iter_rows(values_only=True)]

n_lin = len(dados[ABAS_O[0]])
n_col = len(dados[ABAS_O[0]][0])
for aba in ABAS_O:
    assert len(dados[aba]) == n_lin, f'{aba}: n de linhas diferente'
    assert len(dados[aba][0]) == n_col, f'{aba}: n de colunas diferente'

# --- Conferir que a coluna de wavelength e identica nas 4 abas ---
wl = [dados[ABAS_O[0]][i][0] for i in range(1, n_lin)]
for aba in ABAS_O[1:]:
    wl_aba = [dados[aba][i][0] for i in range(1, n_lin)]
    assert wl_aba == wl, f'{aba}: coluna de wavelength difere de {ABAS_O[0]}'

# --- Cabecalho: codigo do fruto sem o sufixo de orientacao (TIR1O1 -> TIR1) ---
import re
frutos = []
for h in dados[ABAS_O[0]][0][1:]:
    m = re.match(r'(T[IHS]R\d)', str(h))
    frutos.append(m.group(1))
assert len(frutos) == 21, frutos
assert len(set(frutos)) == 21, 'codigos de fruto repetidos'

# --- Criar a nova aba ---
if NOVA_ABA in wb.sheetnames:
    del wb[NOVA_ABA]
ws_new = wb.create_sheet(NOVA_ABA)
ws_new.append(['Wavelength (nm)'] + frutos)

for i in range(1, n_lin):
    linha = [wl[i - 1]]
    for j in range(1, n_col):
        vals = [dados[aba][i][j] for aba in ABAS_O]
        linha.append(sum(vals) / len(vals))
    ws_new.append(linha)

# --- Posicionar a nova aba logo apos O4 ---
idx_o4 = wb.sheetnames.index(ABAS_O[-1])
wb.move_sheet(NOVA_ABA, offset=(idx_o4 + 1) - wb.sheetnames.index(NOVA_ABA))

wb.save(ARQ)
print(f"Aba '{NOVA_ABA}' criada: {n_lin - 1} comprimentos de onda x {len(frutos)} frutos")
print('Ordem das abas:', wb.sheetnames)
