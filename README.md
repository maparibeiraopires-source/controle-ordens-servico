# Controle de Ordens de Serviço — Streamlit 2026

Painel Streamlit baseado nas regras, filtros e classificações do HTML `leitor_dados_dividido.html`.

## Arquivos
- `app.py`: aplicação completa.
- `requirements.txt`: dependências para Streamlit Community Cloud.
- `.streamlit/secrets.toml.example`: modelo opcional de configuração.

## Publicação no Streamlit Community Cloud
1. Envie `app.py` e `requirements.txt` para o repositório GitHub conectado ao aplicativo.
2. Configure o arquivo principal como `app.py`.
3. Em **App settings > Secrets**, informe as credenciais Supabase, se desejar substituir os valores padrão:
   ```toml
   [supabase]
   os_url = "https://SEU-PROJETO-OS.supabase.co"
   os_key = "SUA_CHAVE_PUBLISHABLE"
   ruas_url = "https://SEU-PROJETO-RUAS.supabase.co"
   ruas_key = "SUA_CHAVE_PUBLISHABLE"
   ```
4. Reinicie o aplicativo.

As chaves publishable/anon precisam ter permissão de leitura (SELECT) nas tabelas `ordens_servico` e `ruas`, conforme as políticas RLS do Supabase.

## Fonte e regras reproduzidas
O HTML de referência consulta:
- Projeto de OS: tabela `ordens_servico`.
- Projeto de cadastro viário: tabela `ruas`.

Regras:
- Capinação: comprimento da via × 2.
- Varrição: comprimento da via × 2.
- Nivelamento: metragem `TERRA` × 80%.
- Manutenção/Reparo em Vias: comprimento cadastrado × 80%.
- Cata-Bagulho: 3,5 toneladas por OS.
- Comprimento cadastrado: metragem de `METRAGEM ESCADARIA/VIELA`, quando positiva; caso contrário, soma de `TERRA`, `BLOQUETE`, `PARALELEPÍPEDO` e `ASFALTO`.
- Área de Ouro Fino: Ouro Fino Paulista, Itrapoá, KM4, Casa Vermelha, Pouso Alegre e Somma.
- ODS 12: Cata-Bagulho.
- ODS 6: Drenagem, Desassoreamento, Limpeza de Boca de Lobo/Caixa de Leão e Troca de Tampa/Reparo de Gradil.
- ODS 11: Nivelamento.
- ODS 15: Manutenção/Reparo em Vias e Manutenção/Limpeza de Mobiliário Urbano.

## Observações importantes
- A aplicação consulta todos os registros por paginação de 1.000 linhas, evitando o limite visual de 1.000 registros.
- Os dados são atualizados automaticamente a cada 5 minutos; o botão da barra lateral limpa o cache e consulta novamente.
- A aplicação filtra os registros de 2026.
- A identificação de números faltantes segue o critério do HTML: lacunas com diferença de até 2 entre números encontrados.
- O acesso aos dados depende das permissões RLS existentes nos dois projetos Supabase.
