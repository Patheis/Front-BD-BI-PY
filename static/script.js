 // Função para filtrar os dados
function filterData() {
    var nameInput = document.getElementById("searchName").value.toLowerCase(); // Pegando o valor da caixa de nome
    var dateInput = document.getElementById("searchDate").value; // Pegando o valor da caixa de data
    var table = document.getElementById("dataTable");
    var rows = table.getElementsByTagName("tr");

    // Iterando pelas linhas da tabela (exceto o cabeçalho)
    for (var i = 1; i < rows.length; i++) {
        var cells = rows[i].getElementsByTagName("td");
        var nameCell = cells[1].textContent.toLowerCase(); // Nome da coluna 2
        var dateCell = cells[3].textContent; // Data da coluna 4

        // Condição para exibir a linha baseada na pesquisa de nome e data
        var nameMatch = nameCell.indexOf(nameInput) > -1;
        var dateMatch = dateCell.indexOf(dateInput) > -1 || dateInput === '';

        if (nameMatch && dateMatch) {
            rows[i].style.display = ""; // Exibe a linha
        } else {
            rows[i].style.display = "none"; // Esconde a linha
        }
    }
}


// Função para alternar entre selecionar arquivos ou pastas
function toggleFileInput() {
    var toggle = document.getElementById('toggleUpload');
    var fileInput = document.getElementById('fileInput');
    var label = document.getElementById('toggleLabel');
    
    if (toggle.checked) {
        // Se o toggle estiver ativado (selecionando pasta)
        fileInput.setAttribute('webkitdirectory', ''); // Ativa o modo de selecionar uma pasta
        fileInput.removeAttribute('multiple'); // Desabilita múltiplos arquivos
        label.textContent = "Selecione uma pasta completa"; // Altera o texto do rótulo
    } else {
        // Se o toggle estiver desativado (selecionando um arquivo único)
        fileInput.removeAttribute('webkitdirectory'); // Desativa o modo de pasta
        fileInput.removeAttribute('multiple', ''); // Garante que apenas um arquivo será aceito
        label.textContent = "Selecione um arquivo XML"; // Altera o texto do rótulo
    }
}







