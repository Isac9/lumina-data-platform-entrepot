-- Calendrier : une ligne par jour, de 2023 à 2027.

select
    jour::date                                    as date_jour,
    extract(year from jour)::int                  as annee,
    extract(quarter from jour)::int               as trimestre,
    extract(month from jour)::int                 as mois,
    (array['Janvier','Février','Mars','Avril','Mai','Juin','Juillet',
           'Août','Septembre','Octobre','Novembre','Décembre'])[extract(month from jour)::int] as nom_mois,
    to_char(jour, 'YYYY-MM')                      as annee_mois,
    extract(week from jour)::int                  as semaine_iso,
    extract(isodow from jour)::int                as jour_semaine,
    extract(isodow from jour) in (6, 7)           as est_weekend,
    date_trunc('month', jour)::date               as debut_mois
from generate_series(date '2023-01-01', date '2027-12-31', interval '1 day') as jour
