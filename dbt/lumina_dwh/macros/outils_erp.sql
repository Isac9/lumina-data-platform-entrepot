{#
  Les ERP des pays n'écrivent pas les dates et montants de la même façon :
    CI : 15/03/2025   et  125000
    SN : 2025-03-15   et  125000
    BF : 15/03/2025   et  125 000
  Ces macros remettent tout au même format.
#}

{% macro convertir_date_erp(colonne) %}
    case
        when {{ colonne }} ~ '^\d{4}-\d{2}-\d{2}$' then to_date({{ colonne }}, 'YYYY-MM-DD')
        else to_date({{ colonne }}, 'DD/MM/YYYY')
    end
{% endmacro %}

{% macro convertir_montant_erp(colonne) %}
    regexp_replace({{ colonne }}, '[^0-9.-]', '', 'g')::numeric
{% endmacro %}
