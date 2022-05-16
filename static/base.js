function openCart() {
    $("#cart-container").toggle(750);
}

function openComplaints() {
    $("#complaint-container").toggle(1000);
}

$("#review").click(function(){
  $("reviewtext").hide();
});

// function openCheckout(){
//     $("#gtc").click(function() {
//     $("#cart").slideUp(500);
//     $("#checkout").slideDown(500);
//     });
// }