export function loadSettingsSection(container) {
  container.innerHTML = `
    <div id="main-content">
      <h2>Настройки</h2>
      <p>Выберите тему:</p>
      <div id="theme-switcher">
        <div class="theme-previews">

          <div class="theme-preview" data-theme="light">
            <div class="preview-container theme-light">
              <div class="preview-header">Мой сайт</div>
              <div class="preview-body">
                <div class="preview-sidebar"></div>
                <div class="preview-main"></div>
              </div>
              <div class="preview-footer">©</div>
            </div>
          </div>

          <div class="theme-preview" data-theme="dark">
            <div class="preview-container theme-dark">
              <div class="preview-header">Мой сайт</div>
              <div class="preview-body">
                <div class="preview-sidebar"></div>
                <div class="preview-main"></div>
              </div>
              <div class="preview-footer">©</div>
            </div>
          </div>

          <div class="theme-preview" data-theme="sepia">
            <div class="preview-container theme-sepia">
              <div class="preview-header">Мой сайт</div>
              <div class="preview-body">
                <div class="preview-sidebar"></div>
                <div class="preview-main"></div>
              </div>
              <div class="preview-footer">©</div>
            </div>
          </div>

          <div class="theme-preview" data-theme="cyber">
            <div class="preview-container theme-cyber">
              <div class="preview-header">Мой сайт</div>
              <div class="preview-body">
                <div class="preview-sidebar"></div>
                <div class="preview-main"></div>
              </div>
              <div class="preview-footer">©</div>
            </div>
          </div>

        </div>
      </div>
    </div>
  `;
}
