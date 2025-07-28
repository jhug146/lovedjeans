$(document).ready(function() {
    $("#item-specifics-list").children("li").on("click", function() {
        console.log($("#item-specifics-list").children("li"))
        $("#item-specifics-list").children("li").each(function() {
            $(this).children("button").css({
                "border-bottom": "thin solid black",
                "background-color": "#133e72",
            });
            $(this).children("button").children("h5").css("color", "white");
        });
        $(this).children("button").css({
            "background-color": "white",
            "border-bottom": "none"
        })
        $(this).children("button").children("h5").css("color", "black");
        $(".spe-list").css("display", "none");
        let category = $(this).children("button").children("h5").text().substr(0,3).toLowerCase();
        $("#" + category + "-list").css("display", "block");
    });
})
function check_device() {
    if (window.matchMedia("(max-width: 800px)").matches) {
        $("#image-left").css("display","none");
        $("#image-right").css("display","none");
        return false;
    }
    return true;
}
function move_image(amount) {
    if (!check_device()) {
        return 0;
    }
    let new_image = amount + current_image;
    if (new_image >= 0 && new_image < item_images.length) {
        $("#main-image").attr("src", item_images[new_image]);
        current_image = new_image;
    }
    if (new_image === 0) {
        $("#image-left").css("display","none");
        $("#image-right").css("display","block")
    } else if (new_image === (item_images.length - 1)) {
        $("#image-right").css("display","none");
        $("#image-left").css("display","block")
    } else {
        $("#image-right,#image-left").css("display","block");
    }
}
$(".small-img-div").on("click", function () {
    let image = $(this).children("img").attr("src");
    $("#main-image").attr("src", image);
});
$('#image-left').on("click", function() {
    move_image(-1);
})
$('#image-right').on("click", function() {
    move_image(1);
})
$('button#add-to-cart').click(function () {
    if ($('button#add-to-cart').text() === "Add to Cart") {
        add_to_cart($(this), true);
    }
});
$('button#buy-it-now').click(function () {
    add_to_cart($(this), false);
});
$(document).ready(function () {
    move_image(0);
})
$(window).resize(function () {
    check_device();
})
$("#search-input").on("keypress", function (e) {
    if (e.which === 13) {
        location.href = "/items/?search=" + $("#search-input").val();
    }
});