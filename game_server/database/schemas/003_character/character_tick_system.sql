-- Таблица активных авто-сессий персонажа
CREATE TABLE IF NOT EXISTS auto_sessions (
    character_id integer NOT NULL,
    active_category TEXT NOT NULL,
    next_tick_at TIMESTAMPTZ NOT NULL,
    last_tick_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_character FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_auto_sessions_next_tick_at ON auto_sessions(next_tick_at);

-- Таблица итоговой агрегации тиков (почасовая)
CREATE TABLE IF NOT EXISTS tick_summary (
    id SERIAL PRIMARY KEY,
    character_id integer NOT NULL,  -- Используем integer для character_id
    hour_block TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    tick_count INTEGER NOT NULL,
    mode TEXT NOT NULL,
    summary_data JSONB NOT NULL,
    CONSTRAINT fk_tick_summary_character FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE  -- Внешний ключ на таблицу characters
);

CREATE INDEX IF NOT EXISTS idx_tick_summary_character_time ON tick_summary(character_id, hour_block);

-- Таблица событий тиков (сырые события в Redis-подобном виде)
CREATE TABLE IF NOT EXISTS tick_events (
    id SERIAL PRIMARY KEY,
    character_id integer NOT NULL,  -- Используем integer для character_id
    event_time TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    event_data JSONB NOT NULL,
    CONSTRAINT fk_tick_events_character FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE  -- Внешний ключ на таблицу characters
);

CREATE INDEX IF NOT EXISTS idx_tick_events_character ON tick_events(character_id);
CREATE INDEX IF NOT EXISTS idx_tick_events_time ON tick_events(event_time);


CREATE TABLE finish_handlers (
    batch_id VARCHAR(255) PRIMARY KEY, -- Уникальный идентификатор пакета
    task_type VARCHAR(100) NOT NULL, -- Тип задачи (exploration, crafting и т. д.)
    completed_tasks INT DEFAULT 0, -- Количество выполненных задач
    failed_tasks JSONB, -- 🔥 Список проваленных задач в JSON
    status VARCHAR(50) NOT NULL, -- Итоговый статус (success, failed, partial)
    error_message TEXT, -- Сообщение об ошибке (если есть)
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Дата завершения
    processed_by_coordinator BOOLEAN DEFAULT FALSE -- ✅ Флаг обработки координатором
);

-- 🔹 Индексы для быстрого поиска
CREATE INDEX idx_task_type ON finish_handlers(task_type);
CREATE INDEX idx_status ON finish_handlers(status);
CREATE INDEX idx_timestamp ON finish_handlers(timestamp);
CREATE INDEX idx_processed_coordinator ON finish_handlers(processed_by_coordinator);
