$(document).ready(function() {
  $('.slider').slick({
    slidesToShow: 5,
    slidesToScroll: 1,
    prevArrow: '<button type="button" class="slick-prev"></button>',
    nextArrow: '<button type="button" class="slick-next"></button>',
    infinite: true,
    speed: 500
  });

  $('.option input[type="radio"]').change(function() {
    var selectedImage = $(this).val();

    $.ajax({
      url: '/selected-image',
      type: 'POST',
      data: { image: selectedImage },
      success: function(response) {
        // Handle the server response here
        console.log(response);
      },
      error: function(error) {
        // Handle any errors here
        console.log(error);
      }
    });
  });
});
