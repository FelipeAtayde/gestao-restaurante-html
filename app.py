
import streamlit as st
import pandas as pd
import unidecode
from io import BytesIO

st.set_page_config(page_title="Análise de Maiores Vendas", layout="wide")
st.title("🍽️ Análise de Maiores Vendas")

file_vendas = st.file_uploader("Faça upload da planilha de VENDAS", type=["xlsx"], key="vendas")

def normalizar(texto):
    return unidecode.unidecode(str(texto)).lower().strip()

if file_vendas:
    df = pd.read_excel(file_vendas, skiprows=3)
    df["Itens e Opções"] = df["Itens e Opções"].astype(str).apply(normalizar)

    mult = {
        "- 2 pequenos": 2, "- 3 pequenos": 3, "- 4 pequenos": 4,
        "- 2 grandes": 2, "- 3 grandes": 3, "- 4 grandes": 4
    }
    for k, m in mult.items():
        df.loc[df["Itens e Opções"].str.contains(k), "Quantidade"] *= m

    pequeno = df["Itens e Opções"].str.contains("pequeno") & ~df["Itens e Opções"].str.contains("combo")
    grande = df["Itens e Opções"].str.contains("grande") & ~df["Itens e Opções"].str.contains("combo")
    total_p = int(df.loc[pequeno, "Quantidade"].sum())
    total_g = int(df.loc[grande, "Quantidade"].sum())
    total_geral = total_p + total_g

    pratos = {
        "Boi": lambda x: "boi" in x and "combo" not in x,
        "Parmegiana": lambda x: "parmegiana" in x and "combo" not in x,
        "Strogonoff": lambda x: "strogonoff" in x and "combo" not in x,
        "Feijoada": lambda x: "feijoada" in x and "2 feijoadas" not in x,
        "Tropeiro": lambda x: "tropeiro" in x and "tropeguete" not in x,
        "Tropeguete": lambda x: "tropeguete" in x,
        "Espaguete": lambda x: "espaguete" in x and "tropeguete" not in x,
        "Porco": lambda x: "porco" in x and "combo" not in x,
        "Frango": lambda x: "frango" in x and "parmegiana" not in x and "2 frangos + fritas" not in x
    }

    combos = {
        "Combo Todo Dia": lambda x: "combo todo dia" in x,
        "2 Pratos - À Sua Escolha": lambda x: "2 pratos" in x and "escolha" in x,
        "Combo Supremo": lambda x: "combo supremo" in x,
        "2 Feijoadas": lambda x: "2 feijoadas" in x,
        "2 Frangos + Fritas": lambda x: "2 frangos" in x and "fritas" in x
    }

    refrigerantes = {
        "Coca-Cola Original 350 ml": [["coca", "original", "350"]],
        "Coca-Cola Zero e Sem Açúcar 350 ml": [["coca", "zero", "350"], ["coca", "sem acucar", "350"]],
        "Coca-Cola Original 600 ml": [["coca", "original", "600"]],
        "Coca-Cola Zero 600 ml": [["coca", "zero", "600"], ["coca", "sem acucar", "600"]],
        "Coca-Cola 2 Litros": [["coca", "2l"], ["coca", "2 l"], ["coca", "2litro"]],
        "Guaraná Antarctica 350 ml": [["guarana", "350"]],
        "Guaraná Antarctica 1 Litro": [["guarana", "antarctica", "1l"], ["guarana", "1 l"]],
        "Guaraná Antarctica 2 Litros": [["guarana", "2l"], ["guarana", "2litro"]],
        "Suco": [["suco"]],
        "Refrigerante Mate Couro 1 Litro": [["mate couro", "1l"], ["mate couro", "1 litro"]]
    }

    def contem_tags(texto, listas):
        return any(all(tag in texto for tag in tags) for tags in listas)

    resumo = []
    for nome, cond in pratos.items():
        f = df["Itens e Opções"].apply(cond)
        qtd = int(df.loc[f, "Quantidade"].sum())
        val = df.loc[f, "Valor Total"].sum()
        if qtd > 0:
            resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": f"R$ {val:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")})

    for nome, cond in combos.items():
        f = df["Itens e Opções"].apply(cond)
        qtd = int(df.loc[f, "Quantidade"].sum())
        val = df.loc[f, "Valor Total"].sum()
        if qtd > 0:
            resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": f"R$ {val:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")})

    for nome, tags in refrigerantes.items():
        f = df["Itens e Opções"].apply(lambda x: contem_tags(x, tags))
        qtd = int(df.loc[f, "Quantidade"].sum())
        val = df.loc[f, "Valor Total"].sum()
        if qtd > 0:
            resumo.append({"Categoria": nome, "Quantidade": qtd, "Valor Total": f"R$ {val:,.2f}".replace(".", "X").replace(",", ".").replace("X", ",")})

    resumo_df = pd.DataFrame(resumo)
    resumo_df["Valor Num"] = resumo_df["Valor Total"].str.replace("R\$ ", "", regex=True).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
    resumo_df = resumo_df.sort_values(by="Valor Num", ascending=False).drop(columns="Valor Num")

    st.subheader("Resumo de Pequenos e Grandes")
    st.write(f"Pequeno: {total_p}")
    st.write(f"Grande: {total_g}")
    st.write(f"Total: {total_geral}")

    st.subheader("📋 Resumo Final Agrupado")
    st.dataframe(resumo_df, use_container_width=True)

    excel_vendas = BytesIO()
    resumo_df.to_excel(excel_vendas, index=False, engine='openpyxl')
    st.download_button("📥 Baixar Análise de Vendas (.xlsx)", data=excel_vendas.getvalue(), file_name="analise_maiores_vendas.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
