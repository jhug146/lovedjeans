$.ajaxSetup({ 
    beforeSend: function(xhr, settings) {
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = jQuery.trim(cookies[i]);
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
        }
    } 
});

function round2dp(number) {
    return Math.round((number + Number.EPSILON) * 100) / 100
}

$('img.remove-icon').click(function () {
    $.post(
        '/remove_from_cart/', {
            'sku' : $(this).siblings('.hidden').text()
        },
        function (data) {
            $('#table-row-' + data).remove();
            var total = 0;
            rows = Object.values($('#checkout-table>tbody').children());
            for (let i=0; i<rows.length; i+=1) {
                row = rows[i]
                let price = $(row).children('.item-price-cell').children('div').children('p').text();
                if (price) {
                    price = Number(price.substr(1))
                    total = total + price;
                }
            }
            $('#cart-total-price').text('Total: £' + round2dp(total).toString());
            fix_checkout_display();
            if (rows.length === 3) {
                $('#checkout-table').children().remove();
                $('#checkout-table').css({'background-color': '#133e72'});
                $('#checkout-table').html("<p id='cart-empty' style='color:white'>Your cart is currently empty</p><a style='color:white' id='cart-empty-link' href=" + $("#items-url-container").text() + ">Click here to continue shopping</a>")
                $('#proceed-checkout').remove();
                $('#cart-total-price').remove();
            }    
        }
    );
})