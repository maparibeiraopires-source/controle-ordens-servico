# CONTROLE DE ORDENS DE SERVIÇO — 2026

Versão Streamlit + Plotly com visual em cards/gráficos inspirado em Power BI.

## Correção principal
A contagem foi alinhada à sequência do HTML original:

1. consulta todas as páginas do Supabase (`limit=1000` + `offset`);
2. lê `data_solicitacao` usando os mesmos nomes/campo de fallback;
3. interpreta ISO e `dd/mm/yyyy` na mesma ordem do HTML;
4. mantém apenas registros de 2026;
5. no período selecionado, considera OS válida somente quando o campo OS é numérico;
6. o processamento de ruas é separado da contagem de OS válidas.

O painel também possui uma seção **Auditoria da contagem** para mostrar onde uma eventual diferença aparece.

## Executar no Windows
Use `INICIAR_CONTROLE_OS.bat` ou:

```bash
python -m streamlit run app.py
```
