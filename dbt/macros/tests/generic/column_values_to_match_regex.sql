{% test column_values_to_match_regex(model, column_name, regex) %}

select *
from {{ model }}
where
    {{ column_name }} is not null
    and not regexp_contains(
        cast({{ column_name }} as string),
        r'{{ regex }}'
    )

{% endtest %}
