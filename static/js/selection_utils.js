function initSelection(itemName, masterId) {
  const master = document.getElementById(masterId);
  const items = document.getElementsByName(itemName);
  function updateState() {
    let checked = 0;
    for (let cb of items) { if (cb.checked) checked++; }
    if (checked === 0) {
      master.checked = false;
      master.indeterminate = false;
    } else if (checked === items.length) {
      master.checked = true;
      master.indeterminate = false;
    } else {
      master.checked = false;
      master.indeterminate = true;
    }
  }
  master.addEventListener('change', function () {
    for (let cb of items) { cb.checked = master.checked; }
    updateState();
  });
  for (let cb of items) {
    cb.addEventListener('change', updateState);
  }
  updateState();
}
