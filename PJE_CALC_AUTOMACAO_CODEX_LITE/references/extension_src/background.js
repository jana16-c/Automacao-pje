// Função para criar os menus de contexto com títulos dinâmicos
async function createContextMenus() {
  // Obtém informações sobre o sistema operacional
  const platformInfo = await browser.runtime.getPlatformInfo();
  const isMac = platformInfo.os === "mac";

  // Define as teclas de atalho com base no sistema operacional
  const horizontalShortcut = isMac ? "Command+Alt+H" : "Ctrl+Alt+H";
  const verticalShortcut = isMac ? "Command+Alt+V" : "Ctrl+Alt+V";

  // Remove todos os itens de menu de contexto existentes
  browser.contextMenus.removeAll();

  // Cria o menu pai "Copiar e Colar no Pje-Calc"
  browser.contextMenus.create({
    id: "pje-calc-menu",
    title: "Copiar e Colar no Pje-Calc",
    contexts: ["editable"],
    documentUrlPatterns: [
      "*://*/*pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "*://*/*pjecalc/pages/calculo/parametrizar-ocorrencia.jsf*", // Ocorrências de Verbas
      "*://*/*pjecalc/pages/calculo/parametrizar-fgts.jsf*", // Ocorrências de FGTS
      "*://*/*pjecalc/pages/calculo/inss/parametrizar-inss.jsf*", // Ocorrências de INSS
      "http://localhost:9257/pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "http://localhost:9257/pjecalc/pages/calculo/parametrizar-ocorrencia.jsf*", // Ocorrências de Verbas
      "http://localhost:9257/pages/calculo/parametrizar-fgts.jsf*", // Ocorrências de FGTS
      "http://localhost:9257/pages/calculo/inss/parametrizar-inss.jsf*", // Ocorrências de INSS
      "https://localhost:9257/pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "https://localhost:9257/pjecalc/pages/calculo/parametrizar-ocorrencia.jsf*", // Ocorrências de Verbas
      "https://localhost:9257/pages/calculo/parametrizar-fgts.jsf*", // Ocorrências de FGTS
      "https://localhost:9257/pages/calculo/inss/parametrizar-inss.jsf*" // Ocorrências de INSS
    ]
  });

  // Cria o item de menu de contexto para colagem vertical (dentro do menu pai)
  browser.contextMenus.create({
    id: "paste-vertical",
    parentId: "pje-calc-menu", // Define o menu pai
    title: `Colar na Vertical (${verticalShortcut})`, // Título dinâmico
    contexts: ["editable"],
    documentUrlPatterns: [
      "*://*/*pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "*://*/*pjecalc/pages/calculo/parametrizar-ocorrencia.jsf*", // Ocorrências de Verbas
      "*://*/*pjecalc/pages/calculo/parametrizar-fgts.jsf*", // Ocorrências de FGTS
      "*://*/*pjecalc/pages/calculo/inss/parametrizar-inss.jsf*", // Ocorrências de INSS
      "http://localhost:9257/pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "http://localhost:9257/pjecalc/pages/calculo/parametrizar-ocorrencia.jsf*", // Ocorrências de Verbas
      "http://localhost:9257/pages/calculo/parametrizar-fgts.jsf*", // Ocorrências de FGTS
      "http://localhost:9257/pages/calculo/inss/parametrizar-inss.jsf*", // Ocorrências de INSS
      "https://localhost:9257/pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "https://localhost:9257/pjecalc/pages/calculo/parametrizar-ocorrencia.jsf*", // Ocorrências de Verbas
      "https://localhost:9257/pages/calculo/parametrizar-fgts.jsf*", // Ocorrências de FGTS
      "https://localhost:9257/pages/calculo/inss/parametrizar-inss.jsf*" // Ocorrências de INSS
    ],
    icons: {
      "16": "icons/arrow-down.png" // Ícone de seta para baixo (16x16 pixels)
    }
  });

  // Cria o item de menu de contexto para colagem horizontal (dentro do menu pai)
  browser.contextMenus.create({
    id: "paste-horizontal",
    parentId: "pje-calc-menu", // Define o menu pai
    title: `Colar na Horizontal (${horizontalShortcut})`, // Título dinâmico
    contexts: ["editable"],
    documentUrlPatterns: [
      "*://*/*pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "http://localhost:9257/pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "https://localhost:9257/pjecalc/pages/calculo/historico-salarial.jsf*" // Páginas de histórico salarial
    ],
    icons: {
      "16": "icons/arrow-right.png" // Ícone de seta para a direita (16x16 pixels)
    }
  });

  // Cria o item de menu de contexto para configurações (dentro do menu pai)
  browser.contextMenus.create({
    id: "open-options",
    parentId: "pje-calc-menu", // Define o menu pai
    title: "Configurações",
    contexts: ["editable"],
    documentUrlPatterns: [
      "*://*/*pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "*://*/*pjecalc/pages/calculo/parametrizar-ocorrencia.jsf*", // Ocorrências de Verbas
      "*://*/*pjecalc/pages/calculo/parametrizar-fgts.jsf*", // Ocorrências de FGTS
      "*://*/*pjecalc/pages/calculo/inss/parametrizar-inss.jsf*", // Ocorrências de INSS
      "http://localhost:9257/pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "http://localhost:9257/pjecalc/pages/calculo/parametrizar-ocorrencia.jsf*", // Ocorrências de Verbas
      "http://localhost:9257/pages/calculo/parametrizar-fgts.jsf*", // Ocorrências de FGTS
      "http://localhost:9257/pages/calculo/inss/parametrizar-inss.jsf*", // Ocorrências de INSS
      "https://localhost:9257/pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "https://localhost:9257/pjecalc/pages/calculo/parametrizar-ocorrencia.jsf*", // Ocorrências de Verbas
      "https://localhost:9257/pages/calculo/parametrizar-fgts.jsf*", // Ocorrências de FGTS
      "https://localhost:9257/pages/calculo/inss/parametrizar-inss.jsf*" // Ocorrências de INSS
    ],
    icons: {
      "16": "icons/gear.png" // Ícone de engrenagem (16x16 pixels)
    }
  });

  // Cria o item de menu de contexto para instruções de uso (dentro do menu pai)
  browser.contextMenus.create({
    id: "open-help",
    parentId: "pje-calc-menu", // Define o menu pai
    title: "Instruções de Uso",
    contexts: ["editable"],
    documentUrlPatterns: [
      "*://*/*pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "*://*/*pjecalc/pages/calculo/parametrizar-ocorrencia.jsf*", // Ocorrências de Verbas
      "*://*/*pjecalc/pages/calculo/parametrizar-fgts.jsf*", // Ocorrências de FGTS
      "*://*/*pjecalc/pages/calculo/inss/parametrizar-inss.jsf*", // Ocorrências de INSS
      "http://localhost:9257/pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "http://localhost:9257/pjecalc/pages/calculo/parametrizar-ocorrencia.jsf*", // Ocorrências de Verbas
      "http://localhost:9257/pages/calculo/parametrizar-fgts.jsf*", // Ocorrências de FGTS
      "http://localhost:9257/pages/calculo/inss/parametrizar-inss.jsf*", // Ocorrências de INSS
      "https://localhost:9257/pjecalc/pages/calculo/historico-salarial.jsf*", // Páginas de histórico salarial
      "https://localhost:9257/pjecalc/pages/calculo/parametrizar-ocorrencia.jsf*", // Ocorrências de Verbas
      "https://localhost:9257/pages/calculo/parametrizar-fgts.jsf*", // Ocorrências de FGTS
      "https://localhost:9257/pages/calculo/inss/parametrizar-inss.jsf*" // Ocorrências de INSS
    ],
    icons: {
      "16": "icons/help.png" // Ícone de livro (16x16 pixels)
    }
  });
}

// Listener para quando a extensão é instalada ou atualizada
browser.runtime.onInstalled.addListener((details) => {
  // Cria os menus de contexto com títulos dinâmicos
  createContextMenus();
});

// Listener para quando o item de menu é clicado
browser.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "paste-horizontal") {
    // Envia mensagem para o content.js com o tipo de colagem "horizontal"
    browser.tabs.sendMessage(tab.id, { action: "pasteValues", navigationType: "horizontal" });
  } else if (info.menuItemId === "paste-vertical") {
    // Envia mensagem para o content.js com o tipo de colagem "vertical"
    browser.tabs.sendMessage(tab.id, { action: "pasteValues", navigationType: "vertical" });
  } else if (info.menuItemId === "open-options") {
    // Abre a página de opções
    browser.runtime.openOptionsPage();
  } else if (info.menuItemId === "open-help") {
    // Abre a página de ajuda
    browser.tabs.create({ url: browser.runtime.getURL("help.html") });
  }
});

// Listener para comandos de atalho
browser.commands.onCommand.addListener((command) => {
  if (command === "paste-horizontal") {
    // Verifica a URL da aba ativa antes de executar a ação
    browser.tabs.query({ active: true, currentWindow: true }).then((tabs) => {
      if (tabs[0]) {
        const url = tabs[0].url;
        const allowedUrls = [
          "*://*/*pjecalc/pages/calculo/historico-salarial.jsf*",
          "http://localhost:9257/pjecalc/pages/calculo/historico-salarial.jsf*",
          "https://localhost:9257/pjecalc/pages/calculo/historico-salarial.jsf*"
        ];

        // Verifica se a URL da aba ativa corresponde a uma das URLs permitidas
        const isAllowed = allowedUrls.some(allowedUrl => {
          const regex = new RegExp(allowedUrl.replace(/\*/g, '.*'));
          return regex.test(url);
        });

        if (isAllowed) {
          // Envia mensagem para o content.js para colar na horizontal
          browser.tabs.sendMessage(tabs[0].id, { action: "pasteValues", navigationType: "horizontal" });
        } else {
          console.log("A tecla de atalho Ctrl + Alt + H só funciona nas páginas de histórico salarial.");
        }
      }
    });
  } else if (command === "paste-vertical") {
    // Envia mensagem para o content.js para colar na vertical
    browser.tabs.query({ active: true, currentWindow: true }).then((tabs) => {
      if (tabs[0]) {
        browser.tabs.sendMessage(tabs[0].id, { action: "pasteValues", navigationType: "vertical" });
      }
    });
  }
});