-- Ativa Row Level Security em todas as tabelas públicas, sem nenhuma policy.
-- O app conecta como o usuário dono das tabelas (role "postgres" via pooler do Supabase),
-- que ignora RLS por padrão -- então isso não muda o funcionamento do app.
-- O efeito é só bloquear acesso externo via API REST/GraphQL do Supabase (PostgREST),
-- que hoje conseguiria ler tudo (incluindo hashes de senha em "users") se a anon key vazasse.

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.business_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ingredient_price_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recipe_ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.expense_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cash_entries ENABLE ROW LEVEL SECURITY;
