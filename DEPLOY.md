# Como publicar no Streamlit Community Cloud

O Streamlit Community Cloud é gratuito, mas o disco onde o app roda **não é persistente** — se o app dormir por inatividade ou for redeployado, qualquer arquivo local (como `data/app.db`) é apagado. Por isso, para produção é **obrigatório** usar um banco Postgres externo (gratuito, sem cartão) em vez do SQLite local.

## 1. Crie um banco Postgres gratuito (Supabase)

1. Acesse [supabase.com](https://supabase.com) → crie um projeto novo (grátis, sem cartão).
2. Em **Project Settings → Database → Connection string**, copie a URI (formato `postgresql://postgres:SENHA@db.SEUPROJETO.supabase.co:5432/postgres`).

*(Se preferir, [neon.tech](https://neon.tech) funciona do mesmo jeito.)*

## 2. Suba o código para o GitHub

```bash
# dentro da pasta ar-confeitaria-streamlit
git remote add origin https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
git branch -M main
git push -u origin main
```

## 3. Crie os dados iniciais no banco Postgres

Antes (ou depois) de publicar, rode o seed **uma única vez** apontando para o Postgres, do seu computador:

```bash
# Windows PowerShell
$env:DATABASE_URL="postgresql://postgres:SENHA@db.SEUPROJETO.supabase.co:5432/postgres"
$env:LOGIN_USERNAME="seu-usuario"
$env:LOGIN_PASSWORD="sua-senha-forte"
python seed.py
```

⚠️ **Nunca rode `seed.py` de novo depois de já ter vendas/dados reais** — ele apaga receitas, insumos, vendas e caixa antes de recriar os dados de exemplo.

## 4. Publique no Streamlit Community Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io) (mesma conta que você já usa para o outro app).
2. **New app** → selecione o repositório e a branch `main` → arquivo principal: `Home.py`.
3. Antes de clicar em "Deploy", abra **Advanced settings → Secrets** e cole:

   ```toml
   DATABASE_URL = "postgresql://postgres:SENHA@db.SEUPROJETO.supabase.co:5432/postgres"
   ```

4. Clique em **Deploy**. Depois de publicado, você pode revisitar os secrets em qualquer momento em **⋮ → Settings → Secrets**.

## 5. Pronto

O Streamlit te dá uma URL tipo `ar-confeitaria.streamlit.app`. Acesse e entre com o usuário/senha que você definiu no passo 3.

## Trocar a senha depois

Rode o seed de novo (passo 3) só se quiser **resetar tudo**. Para só trocar a senha sem apagar dados reais, use:

```bash
$env:DATABASE_URL="postgresql://..."
python rotate_login_password.py seu-usuario
```

Se você não definir `NEW_LOGIN_PASSWORD`, o script gera uma senha aleatória forte e imprime uma única vez no terminal.
