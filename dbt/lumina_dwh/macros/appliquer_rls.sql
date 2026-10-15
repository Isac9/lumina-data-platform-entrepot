{#
  Row-Level Security (sécurité au niveau des lignes).
  Après la création d'une table, on ajoute une "règle" :
    - un membre de direction_groupe voit tout ;
    - lecteur_ci ne voit que les lignes où code_entite = 'CI', etc.
#}
{% macro appliquer_rls() %}
    alter table {{ this }} enable row level security;
    create policy filtre_par_entite on {{ this }}
        for select
        using (
            pg_has_role(current_user, 'direction_groupe', 'member')
            or code_entite = upper(replace(current_user, 'lecteur_', ''))
        );
{% endmacro %}
