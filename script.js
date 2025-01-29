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


