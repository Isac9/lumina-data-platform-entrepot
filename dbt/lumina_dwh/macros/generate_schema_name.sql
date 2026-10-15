{#
  Par défaut, dbt nommerait les schémas "analytics_staging", "analytics_marts"...
  Cette macro garde des noms simples : "staging", "marts", etc.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
