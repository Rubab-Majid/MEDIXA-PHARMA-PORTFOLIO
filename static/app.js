document.addEventListener("DOMContentLoaded", function () {
    const navToggle = document.querySelector(".nav-toggle");
    const navbar = document.querySelector(".navbar");

    if (navToggle && navbar) {
        navToggle.addEventListener("click", function () {
            const isOpen = navbar.classList.toggle("open");
            navToggle.setAttribute("aria-expanded", String(isOpen));
            navToggle.setAttribute("aria-label", isOpen ? "Close navigation" : "Open navigation");
        });

        navbar.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", function () {
                navbar.classList.remove("open");
                navToggle.setAttribute("aria-expanded", "false");
                navToggle.setAttribute("aria-label", "Open navigation");
            });
        });
    }

    const medicineSelect = document.getElementById("medicine_id");
    const balanceInput = document.getElementById("available_balance");
    const costInput = document.getElementById("average_cost");
    const quantityInput = document.getElementById("quantity");
    const sellingPriceInput = document.getElementById("selling_price");
    const profitPreview = document.getElementById("profit_preview");

    function calculateProfit() {
        if (!quantityInput || !sellingPriceInput || !profitPreview || !costInput) return;

        const quantity = parseFloat(quantityInput.value || 0);
        const sellingPrice = parseFloat(sellingPriceInput.value || 0);
        const purchasingPrice = parseFloat(costInput.value || 0);
        const totalProfit = (sellingPrice - purchasingPrice) * quantity;

        profitPreview.textContent = totalProfit.toFixed(2);
    }

    function updateSellInformation() {
        if (!medicineSelect) return;

        const selectedOption = medicineSelect.options[medicineSelect.selectedIndex];

        if (!selectedOption || !selectedOption.value) {
            if (balanceInput) balanceInput.value = "0";
            if (costInput) costInput.value = "0.00";
            calculateProfit();
            return;
        }

        const balance = parseFloat(selectedOption.dataset.balance || 0);
        const cost = parseFloat(selectedOption.dataset.cost || 0);

        if (balanceInput) balanceInput.value = balance;
        if (costInput) costInput.value = cost.toFixed(2);
        calculateProfit();
    }

    if (medicineSelect) medicineSelect.addEventListener("change", updateSellInformation);
    if (quantityInput) quantityInput.addEventListener("input", calculateProfit);
    if (sellingPriceInput) sellingPriceInput.addEventListener("input", calculateProfit);

    updateSellInformation();
});

function confirmDelete(medicineName) {
    return window.confirm(
        "Are you sure you want to delete " + medicineName +
        "?\n\nThis will also delete its transaction history."
    );
}
