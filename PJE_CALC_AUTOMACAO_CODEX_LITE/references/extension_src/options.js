document.addEventListener('DOMContentLoaded', function () {
  // Carrega os valores salvos ao abrir a página de configurações
  browser.storage.sync.get(['timeout']).then((result) => {
    // Define os valores padrão se não houver valor salvo
    document.getElementById('timeout').value = result.timeout || 10;
  }).catch((error) => {
    console.error("Erro ao recuperar valor do storage:", error);
  });

  // Salva os valores quando o botão de salvar é clicado
  document.getElementById('save').addEventListener('click', function () {
    const timeout = document.getElementById('timeout').value;

    if (timeout && !isNaN(timeout)) {
      browser.storage.sync.set({
        timeout: parseInt(timeout, 10),
      }).then(() => {
        alert('Configurações salvas!');
      }).catch((error) => {
        console.error("Erro ao salvar valor no storage:", error);
      });
    } else {
      alert("Por favor, insira um valor válido.");
    }
  });
});