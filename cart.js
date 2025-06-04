document.addEventListener('DOMContentLoaded', function () {
    const sizeSelect = document.getElementById('size-select');

    if (sizeSelect) {
        sizeSelect.addEventListener('change', function () {
            const selectedSize = this.value;
            const updateButtons = document.getElementsByClassName('update-cart');

            for (let i = 0; i < updateButtons.length; i++) {
                updateButtons[i].setAttribute('data-size', selectedSize); 
            }
        });
    }

    const updatebtns = document.getElementsByClassName('update-cart');

    for (let i = 0; i < updatebtns.length; i++) {
        updatebtns[i].addEventListener('click', function () {
            const productid = this.dataset.product;
            const action = this.dataset.action;
            const size = this.dataset.size || 'M';  

            if (user === 'AnonymousUser') {
                addCookieItem(productid,action,size);  
            } else {
                updateUserOrder(productid,action,size);
            }
        });
    }
});

function addCookieItem(productid,action,size) {
    let cartkey = productid + '_' + size;
    if (action === 'add') {
        if (cart[cartkey] === undefined) {
            cart[cartkey] = { 'quantity': 1, 'size':size};
        } else {
            cart[cartkey]['quantity'] += 1;
        }
    }

    if (action === 'remove') {
        if (cart[cartkey] !== undefined) {
            cart[cartkey]['quantity'] -= 1;
            if (cart[cartkey]['quantity'] <= 0) {
                delete cart[cartkey];
            }
        }
    }

    document.cookie = 'cart=' + JSON.stringify(cart) + ";path=/";
}

function updateUserOrder(productid, action, size) {
    console.log('User is logged in, sending data...');
    console.log(productid, action, size);

    const url = '/update-item/';
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ 'productid': productid, 'action': action, 'size': size })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Response data:', data);

        let qtyElement = document.getElementById(`item-quantity-${productid}-${size}`);
        if (qtyElement) {
            qtyElement.innerText = data.itemquantity;
        }

        let totalElement = document.getElementById(`item-total-${productid}-${size}`);
        if (totalElement) {
            totalElement.innerText = data.itemprice;
        }


        let cartTotalElement = document.getElementById('cart-total');
        if (cartTotalElement) {
            cartTotalElement.innerText = data.cartTotal;
        }


        let cartQtyElements = document.getElementsByClassName('cart-items-count');
        for (let i = 0; i < cartQtyElements.length; i++) {
            cartQtyElements[i].innerText = data.cartItems;
        }

        if (data.itemquantity === 0) {
            let itemRow = document.getElementById(`item-row-${productid}-${size}`);
            if (itemRow) {
                itemRow.remove();
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
