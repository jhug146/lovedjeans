$("#mobile-search-form").on("click", function(e) {
    if ($("#side-form").css("display") === "none") {
        $("#side-form").css("display", "block")
    } else {
        $("#side-form").css("display", "none")
    }
})
$('#main-form form input:not(#search-input),select').on("change", function (e) {
    if (!e.target.id.includes('page-num')) {
        $('#page-num').attr('value', '1')
    }
    $(this).closest('form').submit();
});
$("#search-input").on("keypress", function (e) {
    if (e.which === 13) {
        if (!e.target.id.includes('page-num')) {
            $('#page-num').attr('value', '1')
        }
        $(this).closest('form').submit();
    }
});
$('button.products-button').click(function (e) {
    e.preventDefault();

    let price = $(this).siblings('.product-price').text().substr(1);
    let title = $(this).siblings('.title-jquery').children('h3').text();
    let sku = $(this).siblings('.hidden').text();
    $.post(
        '/add_to_cart/',
        {
            'price': price,
            'title': title,
            'sku': sku
        },
        function (raw_data) {
            let data = JSON.parse(raw_data);
            if (!data["full"]) {
                let added_div = $('#pc-' + data["SKU"]);
                added_div.children('.products-button').text('Added To Cart');
                added_div.children('.products-button').css({
                    'background-color': '#d82736',
                    'cursor': 'auto'
                });
                added_div.children('.view-cart-hidden').css({
                    'display': 'block',
                    'text-decoration': 'underline'
                });
                fix_checkout_display();
            } else {
                alert("Cart is full");
            }
        }
    );
})