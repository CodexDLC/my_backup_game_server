# 3. Расчёт ΔXP и применение порогов

**Цель:** для каждого активного навыка использовать `base_xp` (2×main + 1×secondary) и применить:

* `PLUS`: `xp += base_xp`
* `MINUS`: `xp -= floor(base_xp/2)`

1. **Таблица skill\_base\_xp** хранит `base_xp` на персонажа и навык.
2. **Порог:** проверять только порог для `level+1` из `skill_unlocks`.
3. **Carry-over:** остаток XP сохраняется.
4. **Логика:** обновление XP, запись в `progression_ticks`, проверка и повышение уровня.
5. **Тесты:** граничные SPECIAL, точность порога.
6. **Логирование:**

   * XP-изменения: `character_id`, `skill_id`, `old_xp`, `new_xp`, `delta`, `level_up`.
   * Запись в `progression_ticks`, ошибки порогов.
7. **Метрики Prometheus:**

   * `xp_update_duration_seconds`
   * `xp_updated_total`
   * `level_ups_total`
   * `xp_update_errors_total`
