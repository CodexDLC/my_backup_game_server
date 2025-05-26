# 2. Фильтрация активных навыков

**Цель:** на каждом тике выбирать только навыки со `progress_state` = `MINUS` или `PLUS` и обеспечивать порядок: сначала `MINUS`, затем `PLUS`.

1. **SQL-запрос:**

   ```sql
   SELECT skill_id, level, xp, progress_state
   FROM character_skills
   WHERE character_id = :id
     AND progress_state <> 'PAUSE'
   ORDER BY CASE WHEN progress_state='MINUS' THEN 0 ELSE 1 END;
   ```

2. **Индекс:** `CREATE INDEX ON character_skills(character_id, progress_state)`.

3. **Порядок обработки:**

   * Сначала деградация (`MINUS`), затем начисление (`PLUS`).

4. **Тесты:** проверка выборки и сортировки.

5. **Логирование:**

   * Выборка навыков: количество, прогресс-статус.
   * Отдельные ошибки при доступе к `character_skills`.

6. **Метрики Prometheus:**

   * `active_skills_selected_total`
   * `active_skills_selection_duration_seconds`
   * `active_skills_selection_errors_total`



'PAUSE' `MINUS` `PLUS`