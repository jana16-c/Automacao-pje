function formatValue(value) {
  // Remove qualquer caractere que não seja número ou vírgula
  value = value.replace(/[^0-9,]/g, '');

  // Substitui a vírgula por ponto para facilitar o cálculo
  value = value.replace(',', '.');

  // Converte para número
  let number = parseFloat(value);

  // Se o valor não for um número válido, retorna '0,00'
  if (isNaN(number)) {
    return '0,00';
  }

  // Converte o número para string e separa a parte inteira da decimal
  let [integerPart, decimalPart] = number.toString().split('.');

  // Se não houver parte decimal, define como '00'
  if (!decimalPart) {
    decimalPart = '00';
  } else if (decimalPart.length < 2) {
    // Se a parte decimal tiver menos de 2 dígitos, completa com zeros
    decimalPart = decimalPart.padEnd(2, '0');
  }

  // Retorna o valor formatado com vírgula como separador decimal
  return `${integerPart},${decimalPart}`;
}


// Função para simular a tecla Tab (navegação horizontal)
function navigateHorizontally() {
  const inputs = Array.from(document.querySelectorAll('input[type="text"]'));
  const currentIndex = inputs.indexOf(document.activeElement);

  if (currentIndex !== -1 && currentIndex < inputs.length - 1) {
    inputs[currentIndex + 1].focus();
  } else if (currentIndex === inputs.length - 1) {
    inputs[0].focus();
  }
}

// Função para simular a tecla Down (navegação vertical)
function navigateVertically() {
  const event = new KeyboardEvent('keydown', {
    key: 'ArrowDown',
    code: 'ArrowDown',
    keyCode: 40,
    which: 40,
    bubbles: true
  });
  document.activeElement.dispatchEvent(event);
}

// Função principal para colar valores
function pasteValues(navigationType = 'vertical') {
  if (!navigator.clipboard) {
    alert("Seu navegador não suporta a API de área de transferência.");
    return;
  }

  browser.storage.sync.get(['timeout']).then((result) => {
    const timeout = result.timeout || 10;

    navigator.clipboard.readText().then(text => {
      if (!text || text.trim() === "") {
        alert("Nenhum texto encontrado na área de transferência. Copie os valores antes de usar a extensão.");
        return;
      }

      const lines = text.split('\n').filter(line => line.trim() !== '');

      if (lines.length === 0) {
        alert("Nenhum valor válido encontrado na área de transferência.");
        return;
      }

      function pasteNextValue(lineIndex, columnIndex) {
        if (lineIndex < lines.length) {
          const columns = lines[lineIndex].split(/[\t ]+/).filter(col => col.trim() !== '');

          if (columnIndex < columns.length) {
            const formattedValue = formatValue(columns[columnIndex]);
            document.activeElement.value = formattedValue;

            if (navigationType === 'horizontal') {
              navigateHorizontally();
              setTimeout(() => pasteNextValue(lineIndex, columnIndex + 1), timeout);
            } else if (navigationType === 'vertical') {
              navigateVertically();
              setTimeout(() => pasteNextValue(lineIndex + 1, columnIndex), timeout);
            }
          } else {
            setTimeout(() => pasteNextValue(lineIndex + 1, 0), timeout);
          }
        } else {
          console.log("Colagem concluída!");
          //alert("Colagem concluída!");
        }
      }

      pasteNextValue(0, 0);
    }).catch(error => {
      console.error("Erro ao ler a área de transferência:", error);
      alert("Erro ao ler a área de transferência. Verifique se há dados copiados e se a extensão tem permissão para acessar a área de transferência.");
    });
  }).catch(error => {
    console.error("Erro ao recuperar valor do storage:", error);
    alert("Erro ao recuperar configurações. Verifique se as configurações foram salvas corretamente.");
  });
}

// Listener para mensagens enviadas pelo background.js
browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "pasteValues") {
    pasteValues(message.navigationType); // Chama a função de colagem com o tipo de navegação
  }
});