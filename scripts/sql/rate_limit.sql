-- rate_limit.sql
-- Corrige a race condition (TOCTOU) do rate limit antigo, que fazia um
-- SELECT + contagem em Python e só depois decidia se bloqueava o usuário.
-- Duas requisições concorrentes podiam passar pela checagem ao mesmo tempo
-- e furar o limite diário.
--
-- Esta migração cria uma tabela de contadores por (chave, dia) e uma função
-- que incrementa esse contador de forma ATÔMICA usando
-- INSERT ... ON CONFLICT DO UPDATE ... WHERE, que no Postgres é executado
-- sob lock de linha — ou seja, duas chamadas concorrentes nunca conseguem
-- "passar" ao mesmo tempo.
--
-- Aplique este script uma vez no SQL Editor do seu projeto Supabase.

create table if not exists public.limites_diarios (
    chave     text not null,
    dia       date not null default (now() at time zone 'utc')::date,
    contagem  integer not null default 0,
    primary key (chave, dia)
);

-- Função atômica: tenta incrementar o contador do dia para "chave".
-- Retorna TRUE se a tentativa foi aceita (contagem ficou <= p_limite),
-- ou FALSE se o limite já havia sido atingido (nada é incrementado).
create or replace function public.registrar_tentativa_redacao(
    p_chave text,
    p_limite integer
)
returns boolean
language plpgsql
security definer
as $$
declare
    v_contagem integer;
begin
    insert into public.limites_diarios (chave, dia, contagem)
    values (p_chave, (now() at time zone 'utc')::date, 1)
    on conflict (chave, dia) do update
        set contagem = public.limites_diarios.contagem + 1
        where public.limites_diarios.contagem < p_limite
    returning contagem into v_contagem;

    -- Se a cláusula WHERE do UPDATE não bateu (limite já atingido) e não era
    -- um INSERT novo, nenhuma linha é retornada.
    if v_contagem is null then
        return false;
    end if;

    return true;
end;
$$;

-- Permite que o backend (usando a service role key) chame a função via RPC.
grant execute on function public.registrar_tentativa_redacao(text, integer) to service_role;
grant execute on function public.registrar_tentativa_redacao(text, integer) to authenticated;

-- Opcional: limpar contadores de dias antigos periodicamente (ex: via cron/Edge Function)
-- delete from public.limites_diarios where dia < (now() at time zone 'utc')::date - interval '7 days';
