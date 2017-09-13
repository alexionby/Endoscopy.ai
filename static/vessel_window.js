$(function(){

 $(".vessels a").click( function() {
   console.log( this.href.split('_').slice(-1)[0] );
 });

});
