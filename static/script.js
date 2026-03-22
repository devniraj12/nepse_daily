/*
 *   Copyright (c) 2026 SMARTz Developer
 *   All rights reserved.
 */
let allocationChart = null;

document.addEventListener('DOMContentLoaded', () => {
    // Set current date
    document.getElementById('currentDate').innerText = new Date().toLocaleDateString('en-US', { 
        month: 'long', day: 'numeric', year: 'numeric' 
    });

    initChart();
    fetchData();

    document.getElementById('refreshReport').addEventListener('click', async (e) => {
        const btn = e.target;
        btn.innerText = "Sending...";
        await fetch('/api/report');
        btn.innerText = "Report Sent!";
        setTimeout(() => btn.innerText = "Send Telegram Report", 3000);
    });
});

function initChart() {
    const ctx = document.getElementById('allocationPieChart').getContext('2d');
    allocationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['NEPSE', 'Silver', 'Crypto', 'Pokémon', 'Global'],
            datasets: [{
                data: [0, 0, 0, 0, 0],
                backgroundColor: ['#3b82f6', '#c9d1d9', '#f59e0b', '#ec4899', '#8b949e'],
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false, // CRITICAL FIX
            plugins: {
                legend: {
                    display: true,
                    position: 'right',
                    labels: { color: '#8b949e', boxWidth: 12, font: { size: 10 } }
                }
            },
            cutout: '70%'
        }
    });
}

async function fetchData() {
    try {
        const response = await fetch('/api/dashboard_data');
        const data = await response.json();
        
        console.log("Data from API:", data);

        const nprFormatter = new Intl.NumberFormat('en-NP', {
            style: 'currency',
            currency: 'NPR',
            minimumFractionDigits: 0
        });

        // Update Values
        document.getElementById('totalPortfolioValue').innerText = nprFormatter.format(data.total);
        document.getElementById('topAssetName').innerText = data.topAsset;
        document.getElementById('topAssetCategory').innerText = data.topCategory;

        // Update Chart
        allocationChart.data.datasets[0].data = data.allocation;
        allocationChart.update();

        // Update Table
        const tbody = document.getElementById('holdingsBody');
        tbody.innerHTML = data.holdings.map(h => `
            <tr>
                <td><strong>${h.symbol}</strong></td>
                <td><span class="badge ${h.cat}">${h.cat}</span></td>
                <td>${h.qty}</td>
                <td>${nprFormatter.format(h.price)}</td>
                <td><strong>${nprFormatter.format(h.total)}</strong></td>
            </tr>
        `).join('');

    } catch (err) {
        console.error("Dashboard error:", err);
    }
}

async function addNewStock() {
    const payload = {
        symbol: document.getElementById('sym').value,
        qty: parseFloat(document.getElementById('qty').value),
        buy_price: parseFloat(document.getElementById('price').value),
        cat: document.getElementById('cat').value
    };

    const response = await fetch('/api/add_stock', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });

    const result = await response.json();
    if (result.status === "success") {
        alert("Stock Added!");
        loadDashboard(); // Refresh the table automatically!
    } else {
        alert("Error: " + result.message);
    }
}

// This will refresh your data every 1 minute without reloading the whole page
setInterval(() => {
    console.log("Fetching latest market prices...");
    loadDashboard(); 
}, 60000);