document.addEventListener("DOMContentLoaded", function () {
  const ctx = document.getElementById("statusChart");
  if (ctx && chartLabels && chartData) {
    new Chart(ctx, {
      type: "line",
      data: {
        labels: chartLabels,
        datasets: [{
          data: chartData,
          backgroundColor: [
            "rgba(34, 197, 94, 0.6)", // Sent
            "rgba(234, 179, 8, 0.6)",  // Pending
            "rgba(239, 68, 68, 0.6)"   // Failed
          ],
          borderColor: [
            "rgba(34, 197, 94, 1)",
            "rgba(234, 179, 8, 1)",
            "rgba(239, 68, 68, 1)"
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: "bottom"
          }
        }
      }
    });
  } else {
    console.error("No se pudo inicializar el gráfico. Elemento o datos faltantes.");
  }
});