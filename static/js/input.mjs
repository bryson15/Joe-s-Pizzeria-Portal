const AttemptTotalCalculation = () => {
    let rows = document.querySelectorAll("#items .row");
    let total = 0;
    for (let i = 0; i < rows.length; i++) {
        let row = rows[i];
        let quantity = parseFloat(row.querySelector('.input[name="quantity"]').value);
        let price = parseFloat(row.querySelector('#price').textContent);
        if (quantity > 0 && price > 0) {
            total += quantity * price;
        } else {
            return;
        }
    }
    if (commissionRate) {
        total = total * (1 + commissionRate/100);  
    }
    document.querySelector('#total').innerText = total.toFixed(2);
}

var commissionRate; 

document.querySelector(".plus").addEventListener("click", function () {
    let rows = document.querySelectorAll("#items .row");
    let lastRow = rows[rows.length - 1];
    let clonedRow = lastRow.cloneNode(true);
    clonedRow.querySelector(".cross").addEventListener("click", function () {
        if (document.querySelectorAll("#items .row").length > 1) { 
            this.parentNode.remove();
        }
    });

    let dropdown = clonedRow.querySelector('.dropdown');
    dropdown.addEventListener('change', () => {
        clonedRow.querySelector('#price').textContent = dropdown.options[dropdown.selectedIndex].getAttribute('data-price');
        AttemptTotalCalculation();
    });

    clonedRow.querySelector('#qty').addEventListener('blur', () => {
        AttemptTotalCalculation();
    });

    document.querySelector("#items").appendChild(clonedRow);
});
    
document.querySelector(".cross").addEventListener("click", () => {
    if (document.querySelectorAll("#items .row").length > 1) { 
        this.parentNode.remove();
    }
});
  
document.querySelector('input[name="postcode"]').addEventListener('blur', (event) => {
    fetch('/postcode_input', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'postcode=' + encodeURIComponent(event.target.value)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.querySelector('#error').innerText = `Error: ${data.error}`;
            document.querySelector('#result').display = "none";
        } else {
            document.querySelector('#driver-id').innerText = data.driver_id;
            document.querySelector('#commission-rate').innerText = data.commission_rate;
            commissionRate = data.commission_rate;
            AttemptTotalCalculation();
        }
    });
});

let dropdown = document.querySelector('.dropdown');
dropdown.addEventListener('change', () => {
    document.getElementById('price').textContent = dropdown.options[dropdown.selectedIndex].getAttribute('data-price');
    AttemptTotalCalculation();
});

document.querySelector('#qty').addEventListener('change', () => {
    AttemptTotalCalculation();
});

document.querySelector('form').addEventListener('submit', event => {
    event.preventDefault();
    let formData = new FormData(event.target);
    formData.append('driver-id', document.querySelector("#driver-id").innerText);
    if (document.querySelector('#postcode').value !== "" && document.querySelector('#driver-id').innerText == "") {
        document.querySelector('#error').innerText = "Error: Invalid Postcode Entered";
        return;
    }
    formData.append('commission-rate', document.querySelector("#commission-rate").innerText);
    formData.append('store-id', 1155231);
    formData.append('order-total', document.querySelector("#total").innerText);
    let prices = document.querySelectorAll("#price");
    prices.forEach(priceElement => {
        formData.append('item-price', priceElement.innerText);
    });
    fetch('/submit_input', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const error = document.querySelector('#error');
        const result = document.querySelector('#result');
        if (data.error) {
            error.innerText = `Error: ${data.error}`;
            result.style.visibility = "hidden";
        } else {
            error.innerText = "";
            result.style.visibility = "visible";
            result.href = data.result;
            document.querySelector(".result-text").innerText = "Transaction Created: Click To View Data";
        }
    })
});
