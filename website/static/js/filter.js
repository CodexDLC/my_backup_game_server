// filter.js: функции для фильтрации данных и создания UI-элементов фильтров

/**
 * Возвращает массив элементов, отфильтрованных по редкости.
 * @param {Array<Object>} items - исходный массив объектов с полем rarity
 * @param {number|string} rarity - значение редкости или 'all'
 * @returns {Array<Object>} - отфильтрованный массив
 */
export function applyRarityFilter(items, rarity) {
    if (rarity === 'all' || rarity === undefined) return items;
    return items.filter(item => item.rarity === Number(rarity));
  }
  
  /**
   * Создаёт селект для фильтрации по редкости и навешивает обработчик.
   * @param {Array<Object>} items - массив элементов с полем rarity
   * @param {HTMLElement} container - элемент, куда будет вставлен селект
   * @param {Function} onFilterChange - callback, вызываемый с отфильтрованным массивом
   */
  export function setupRarityFilter(items, container, onFilterChange) {
    // Создаём контейнер фильтра
    const filterWrap = document.createElement('div');
    filterWrap.className = 'filter-container';
  
    const label = document.createElement('label');
    label.textContent = 'Фильтр по редкости: ';
    filterWrap.appendChild(label);
  
    const select = document.createElement('select');
    // Опции
    const rarities = [...new Set(items.map(i => i.rarity))].sort((a, b) => a - b);
    const optAll = document.createElement('option'); optAll.value = 'all'; optAll.textContent = 'Все';
    select.appendChild(optAll);
    rarities.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r;
      opt.textContent = r;
      select.appendChild(opt);
    });
  
    // Обработчик изменения
    select.addEventListener('change', () => {
      const filtered = applyRarityFilter(items, select.value);
      onFilterChange(filtered);
    });
  
    filterWrap.appendChild(select);
    container.appendChild(filterWrap);
  }
  