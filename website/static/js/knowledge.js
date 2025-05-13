// knowledge.js: логика раздела «База» (загрузка из базы и MD-подразделов)

import { loadMarkdown } from './markdown.js';

/**
 * Инициализация раздела «База».
 * @param {HTMLElement} contentFrame - контейнер, куда размещается sidebar и контент.
 */
export function initKnowledgeSection(contentFrame) {
    if (!contentFrame) {
        console.error('Ошибка: контейнер для контента не найден');
        return;
    }

    // Конфигурация подразделов «База»
    const sections = [
        { id: 'items', name: 'Предметы' },
        { id: 'mechanics', name: 'Механики', md: 'mechanics.md' },
        { id: 'classes', name: 'Классы', md: 'classes.md' }
    ];

    // Очищаем контейнер и создаём элементы
    contentFrame.innerHTML = '';
    const sidebar = document.createElement('aside');
    sidebar.id = 'sidebar-panel';
    const mainContent = document.createElement('div');
    mainContent.id = 'main-content';

    // Создаём кнопки бокового меню
    sections.forEach(item => {
        const btn = document.createElement('button');
        btn.className = 'sidebar-btn';
        btn.textContent = item.name;
        btn.addEventListener('click', () => handleClick(item, btn, sidebar, mainContent));
        sidebar.appendChild(btn);
    });

    // Добавляем sidebar и контент в контейнер
    contentFrame.appendChild(sidebar);
    contentFrame.appendChild(mainContent);

    // Активируем первый подраздел по умолчанию
    const firstButton = sidebar.querySelector('button');
    if (firstButton) firstButton.click();
}

/**
 * Обработчик клика по подразделу.
 */
function handleClick(item, btn, sidebar, mainContent) {
    // Подсветка активной кнопки
    sidebar.querySelectorAll('.sidebar-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Загружаем контент
    if (item.id === 'items') {
        loadItemsTable(mainContent);
    } else if (item.md) {
        loadMarkdown(item.md, mainContent);
    }
}

/**
 * Загружает и рендерит таблицу предметов из API /knowledge-base/
 */
function loadItemsTable(container) {
    const url = '/knowledge-base/';
    fetch(url)
        .then(res => res.ok ? res.json() : Promise.reject(`Ошибка сети ${res.status}`))
        .then(data => {
            container.innerHTML = '';
            const table = document.createElement('table');
            table.className = 'data-table';
            const thead = table.createTHead();
            const headerRow = thead.insertRow();
            ['Тип', 'Название', 'Цвет', 'Описание'].forEach(text => {
                const th = document.createElement('th');
                th.textContent = text;
                headerRow.appendChild(th);
            });

            const tbody = table.createTBody();
            const typeMap = { weapons: 'Оружие', armor: 'Броня', accessories: 'Аксессуар' };
            Object.keys(typeMap).forEach(key => {
                (data[key] || []).forEach(item => {
                    const row = tbody.insertRow();
                    row.insertCell().textContent = typeMap[key];
                    row.insertCell().textContent = item.name;
                    row.insertCell().textContent = item.color;
                    row.insertCell().textContent = item.description;
                });
            });

            container.appendChild(table);
        })
        .catch(err => {
            console.error(err);
            container.innerHTML = `<p>Ошибка загрузки предметов: ${err}</p>`;
        });
}
