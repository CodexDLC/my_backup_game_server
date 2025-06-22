
# game_server\config\constants\arq.py




# --- Пути к ARQ-задачам (для постановки задач через ArqTaskDispatcher) ---
ARQ_TASK_GENERATE_CHARACTER_BATCH: str = "game_server.Logic.InfrastructureLogic.arq_worker.arq_tasks.arq_character_generation.generate_character_batch_task"
ARQ_TASK_PROCESS_ITEM_GENERATION_BATCH: str = "game_server.Logic.InfrastructureLogic.arq_worker.arq_tasks.arq_item_generation.process_item_generation_batch_task"
ARQ_TASK_PROCESS_EXPLORATION: str = "game_server.Logic.InfrastructureLogic.arq_worker.arq_tasks.arq_tick_coordinator.arq_process_exploration_task" 
ARQ_TASK_PROCESS_TRAINING: str = "game_server.Logic.InfrastructureLogic.arq_worker.arq_tasks.arq_tick_coordinator.arq_process_training_task"   
ARQ_TASK_PROCESS_CRAFTING: str = "game_server.Logic.InfrastructureLogic.arq_worker.arq_tasks.arq_tick_coordinator.arq_process_crafting_task"

