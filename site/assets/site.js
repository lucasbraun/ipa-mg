/* Optional enhancement: every comic remains visible when JavaScript is off. */
const filters = document.querySelectorAll('[data-filter]');
const cards = document.querySelectorAll('[data-category]');
const counter = document.querySelector('.result-count');

for (const button of filters) {
  button.addEventListener('click', () => {
    for (const filter of filters) {
      const selected = filter === button;
      filter.classList.toggle('active', selected);
      filter.setAttribute('aria-pressed', String(selected));
    }
    let visible = 0;
    for (const card of cards) {
      card.hidden = button.dataset.filter !== 'all'
        && card.dataset.category !== button.dataset.filter;
      if (!card.hidden) visible += 1;
    }
    counter.textContent = `${visible} shelf favourites`;
  });
}
