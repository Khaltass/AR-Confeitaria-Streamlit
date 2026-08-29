# A.R Confeitaria — Sistema de Gestão (Streamlit)

Aplicativo web (mobile-first) para substituir a planilha de controle da A.R Confeitaria: precificação de receitas, vendas, fluxo de caixa e relatórios, com histórico completo.

Versão em **Python + Streamlit**, feita para publicar de graça no [Streamlit Community Cloud](https://streamlit.io/cloud). Existe também uma versão em Next.js deste mesmo app (`../ar-confeitaria`) — esta é a que será publicada.

## Stack

- **Streamlit** — interface e navegação (`Home.py` + `pages/`)
- **SQLAlchemy** — acesso ao banco, funciona com SQLite (local) ou Postgres (produção) sem mudar código
- **SQLite local** (`data/app.db`) para desenvolvimento — **Postgres externo obrigatório** para publicar (o disco do Streamlit Cloud não é persistente; ver `DEPLOY.md`)

## Como rodar localmente

Pré-requisito: Python 3.11+.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (PowerShell: .venv\Scripts\Activate.ps1)
pip install -r requirements.txt

python seed.py                  # cria o login e os dados de exemplo
streamlit run Home.py
```

Acesse **http://localhost:8501**.

### Login (criado pelo seed)

Definido pelas variáveis de ambiente `LOGIN_USERNAME` e `LOGIN_PASSWORD` — defina-as antes de rodar `python seed.py`:

```bash
# Windows PowerShell
$env:LOGIN_USERNAME="seu-usuario"
$env:LOGIN_PASSWORD="sua-senha-forte"
python seed.py
```

Se `LOGIN_PASSWORD` não for definida, o seed gera uma senha aleatória e imprime no terminal (não fica salva em nenhum arquivo). O seed apaga qualquer login anterior e cria só esse.

Para trocar a senha depois **sem apagar dados reais**, use `python rotate_login_password.py <usuario>` em vez de rodar o seed de novo.

## Publicar no Streamlit Community Cloud

Veja o passo a passo completo em [DEPLOY.md](DEPLOY.md).

## Estrutura de pastas

```
Home.py                  ponto de entrada: login + dashboard + navegação
auth.py                  login simples usuário/senha
db.py                    conexão com o banco (SQLite local / Postgres via secret)
models.py                modelo do banco de dados (SQLAlchemy)
pricing.py                motor de cálculo de preço (Módulo 2, ver abaixo)
format_utils.py           formatação em R$ e datas dd/mm/aaaa
seed.py                   popula login + dados de exemplo
pages/
  1_Configuracoes.py      Módulo 0
  2_Insumos.py             Módulo 1
  3_Receitas.py            Módulo 2 (cálculo de preço)
  4_Vendas.py              Módulo 3
  5_Caixa.py               Módulo 4
  6_Relatorios.py          Módulo 5
```

## Sobre o cálculo de preço (Módulo 2)

A lógica em [`pricing.py`](pricing.py) é um port exato de `src/lib/pricing.ts` do app Next.js original, que por sua vez replica a fórmula da planilha `precificação_Nova.xlsx`. Mesma ordem de cálculo: custo de materiais → outros custos diretos → custo de mão de obra → total parcial → margem de lucro → impostos → comissões → rateio de custos fixos → preço por unidade → preço do cento.

A constante **1400** usada no rateio de custos fixos foi herdada da planilha original (origem não identificada) e foi mantida exatamente como estava. Editável em Configurações, padrão 1400.

Rodar `python seed.py` imprime no terminal o detalhamento completo do cálculo das duas receitas de exemplo ("Bolo de Chocolate 20cm", rendimento 1, e "Brigadeiro Gourmet", rendimento 10), para conferência.

## Backup dos dados

- **Local (SQLite):** copie o arquivo `data/app.db`.
- **Produção (Postgres/Supabase):** use a ferramenta de backup do próprio provedor (Supabase e Neon têm backup automático nos planos gratuitos com retenção limitada — exporte periodicamente pela tela de Relatórios como reforço).

Também é possível exportar vendas e lançamentos de caixa em CSV pela tela de **Relatórios**.
