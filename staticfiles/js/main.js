$(document).ready(function (e) {
    $('#header-dropdown-button').on('click', function(e) {
        console.log(e)
        $('.header-dropdown-content')[0].classList.toggle('show')
    });
    window.onclick = function(event) {
        if (!event.target.matches('#header-dropdown-button')) {
            dropdown = $('header-dropdown-content');
            if (dropdown.length) {
                if (dropdown.classList.contains('show')) {
                    dropdown.classList.remove('show');
                }
            }
        }
    }
    $('#header-checkout-image').css({"width": $('#header-checkout-image').height()});
});
$(window).resize(function () {
    $('#header-checkout-image').css({"width": $('#header-checkout-image').height()});
})