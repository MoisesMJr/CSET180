function openCart() {
    $("#cart-container").toggle(750);
}

function openReviewText(){
    $("#review").click(function(){
        $("reviewtext").slideDown();
    })
}




// function openCheckout(){
//     $("#gtc").click(function() {
//     $("#cart").slideUp(500);
//     $("#checkout").slideDown(500);
//     });
// }