# game_server/config/constants/redis/item_keys.py

# Шаблон для ключа-контейнера экземпляра предмета (тип: Hash)
KEY_ITEM_INSTANCE_DATA = "world:item_instance:{item_uuid}"

# Имя поля внутри Hash'а, где лежит основной JSON с данными предмета
FIELD_ITEM_INSTANCE_DATA = "data"