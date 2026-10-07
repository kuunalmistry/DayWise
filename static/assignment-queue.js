(() => {
  const metadataContainers = [
    { selector: '#calendarData', rows: '.queue-item', dashboard: true },
    { selector: '#calendarAssignments', rows: '.full-task-row', dashboard: false }
  ];

  const renderChecklists = () => {
    document.querySelectorAll('.queue-subtasks').forEach(list => list.remove());
    for (const container of metadataContainers) {
      const metadata = [...document.querySelectorAll(`${container.selector} > span`)];
      const rows = [...document.querySelectorAll(container.rows)];
      metadata.forEach((assignment, index) => {
        const row = rows[index];
        const subtasks = [...assignment.querySelectorAll('i[data-subtask-id]')];
        if (!row || subtasks.length === 0) return;

        const list = document.createElement('div');
        list.className = 'queue-subtasks';
        list.setAttribute('aria-label', `Subtasks for ${assignment.dataset.title}`);
        for (const subtask of subtasks) {
          const form = document.createElement('form');
          form.className = 'queue-subtask-form';
          form.action = subtask.dataset.url;
          form.method = 'post';

          const button = document.createElement('button');
          const completed = subtask.dataset.completed === 'true';
          button.type = 'submit';
          button.className = `subtask-check${completed ? ' checked' : ''}`;
          button.setAttribute('role', 'checkbox');
          button.setAttribute('aria-checked', String(completed));
          button.setAttribute('aria-label', `${completed ? 'Mark incomplete' : 'Complete'}: ${subtask.dataset.title}`);
          button.innerHTML = '<span class="material-symbols-outlined" aria-hidden="true">check</span>';

          const title = document.createElement('span');
          title.className = `subtask-title${completed ? ' completed' : ''}`;
          title.textContent = subtask.dataset.title;
          form.append(button, title);
          list.append(form);
        }

        const progressBar = row.querySelector(container.dashboard ? '.queue-progress > span' : '.task-progress > span');
        const percentLabel = row.querySelector(container.dashboard ? '.queue-percent' : '.task-progress-label');
        const isAssignmentComplete = Boolean(row.querySelector('.status-badge.completed'));
        const progress = isAssignmentComplete ? 100 : Math.round(
          subtasks.filter(item => item.dataset.completed === 'true').length / subtasks.length * 100
        );
        if (progressBar) progressBar.style.width = `${progress}%`;
        if (percentLabel) percentLabel.textContent = `${progress}% complete`;
        if (!container.dashboard && progressBar && !percentLabel) {
          const label = document.createElement('small');
          label.className = 'task-progress-label';
          label.textContent = `${progress}% complete`;
          progressBar.parentElement.after(label);
        }

        if (container.dashboard) {
          row.querySelector('.queue-progress')?.before(list);
        } else {
          row.querySelector('.task-progress')?.after(list);
        }
      });
    }
  };

  renderChecklists();
  window.addEventListener('assignment-queue-updated', renderChecklists);

  document.addEventListener('submit', async event => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || !form.matches('.queue-subtask-form')) return;
    event.preventDefault();

    const button = form.querySelector('button.subtask-check');
    if (!button) return;

    button.disabled = true;
    try {
      const response = await fetch(form.action, {
        method: 'POST',
        headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' }
      });
      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Request failed (${response.status})`);
      }
      const result = await response.json();
      const completed = Boolean(result.completed);
      document.querySelectorAll('#calendarData i[data-subtask-id], #calendarAssignments i[data-subtask-id]')
        .forEach(item => {
          if (item.dataset.subtaskId === String(result.subtask_id)) {
            item.dataset.completed = String(completed);
          }
        });
      button.setAttribute('aria-checked', String(completed));
      button.setAttribute('aria-label', `${completed ? 'Mark incomplete' : 'Complete'}: ${form.querySelector('.subtask-title').textContent}`);
      button.classList.toggle('checked', completed);
      form.querySelector('.subtask-title').classList.toggle('completed', completed);

      const row = form.closest('.queue-item, .full-task-row');
      const bar = row?.querySelector('.queue-progress > span, .task-progress > span');
      const label = row?.querySelector('.queue-percent, .task-progress-label');
      const done = Boolean(row?.querySelector('.status-badge.completed'));
      const progress = done ? 100 : result.progress;
      if (bar) bar.style.width = `${progress}%`;
      if (label) label.textContent = `${progress}% complete`;
    } catch (error) {
      window.alert(`Could not update this subtask. ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      button.disabled = false;
    }
  });
})();
