/* 
 if(window.location.href.indexOf("/register")>-1){
   setInterval(function(){
    $(".section-title.lines .text").html("Si vous n’êtes pas salarié(e)  de l’une des entreprises ci-dessus, merci de remplir le formulaire :");
    $(".login-providers .text").html("Si vous êtes salarié(e) de Elengy, GRDF, GRTgaz, ou Storengy, créez votre compte en cliquant sur le bouton correspondant :");
   },250);
  }
*/
/*  if(window.location.href.indexOf("/about")>-1){
   setInterval(function(){
    $(".important-dates-item-text.start-date.localized_datetime").html("7 Sept. 2017");
    $(".important-dates-item-text.final-date.localized_datetime").html("18 Nov. 2017");
    $(".icon.fa.fa-thumbs-up").removeClass("fa-thumbs-up").addClass("fa-facebook");
   },250);  
  }
*/
/* jQuery initialize */
;(function ($) {

    "use strict";

    // MutationSelectorObserver represents a selector and it's associated initialization callback.
    var MutationSelectorObserver = function (selector, callback) {
        this.selector = selector;
        this.callback = callback;
    };

    // List of MutationSelectorObservers.
    var msobservers = [];
    msobservers.initialize = function (selector, callback) {

        // Wrap the callback so that we can ensure that it is only
        // called once per element.
        var seen = [];
        var callbackOnce = function () {
            if (seen.indexOf(this) == -1) {
                seen.push(this);
                $(this).each(callback);
            }
        };

        // See if the selector matches any elements already on the page.
        $(selector).each(callbackOnce);

        // Then, add it to the list of selector observers.
        this.push(new MutationSelectorObserver(selector, callbackOnce));
    };

    // The MutationObserver watches for when new elements are added to the DOM.
    var observer = new MutationObserver(function (mutations) {

        // For each MutationSelectorObserver currently registered.
        for (var j = 0; j < msobservers.length; j++) {
            $(msobservers[j].selector).each(msobservers[j].callback);
        }
    });

    // Observe the entire document.
    observer.observe(document.documentElement, {childList: true, subtree: true, attributes: true});

    // Deprecated API (does not work with jQuery >= 3.1.1):
    $.fn.initialize = function (callback) {
        msobservers.initialize(this.selector, callback);
    };
    $.initialize = function (selector, callback) {
        msobservers.initialize(selector, callback);
    };
})(jQuery);
/* end jQuery initialize */

var url_tma = window.location.href;
console.log(url_tma);
if(window.location.href.indexOf("/register")>-1 || window.location.href.indexOf("/login")>-1) {
$("#register-name-desc").initialize(function(){
 $(this).html("Ce nom et ce prénom seront utilisés pour votre attestation de réussite au MOOC.");
});
$(".toggle-form .section-title span.text").initialize(function(){
 if(window.location.href.indexOf("/login")>-1){
  $(this).html("Pas encore inscrit(e) au MOOC Exp&eacute;rience Gaz ?");
 }
});

if(window.location.href.indexOf("/login")>-1) {
  $(".section-title.lines .text").initialize(function(){
   $(this).html('Si vous n’êtes pas salarié(e)  de l’une des entreprises ci-dessous, merci de renseigner vos identifiants MOOC:');
  });
  $(".login-providers .text").initialize(function(){
   $(this).html('Si vous êtes salari&eacute;(e) de Elengy, GRDF, GRTgaz, ou Storengy, merci de cliquer sur le bouton correspondant :');
  });
}
if(window.location.href.indexOf("/register")>-1) {
  $(".section-title.lines .text").initialize(function(){
   $(this).html('Si vous n\'êtes pas salari&eacute;(e)  de l\'une des entreprises ci-dessus, merci de remplir le formulaire :');
  });
  $(".login-providers .text").initialize(function(){
   $(this).html('Si vous êtes salari&eacute;(e) de Elengy, GRDF, GRTgaz, ou Storengy, cr&eacute;ez votre compte en cliquant sur le bouton correspondant :');
  });
}

$('label').initialize(function(){
 var This = $(this);
 var text = This.text();
 if(text.indexOf('Full name') != -1) {
  $(this).html('Nom Prénom *');
 }
 if(text.indexOf('Public username') != -1) {
  $(this).html('Nom d’utilisateur sur le MOOC (pseudo) *');
 }
 if(text.indexOf("J'accepte les Conditions d'utilisation et Code d'honneur de  MOOC Experience Gaz") != -1) {
  $(this).html("J'accepte les conditions générales d'utilisation *");
 }
});
$('#register-username-desc').initialize(function(){
 $(this).html('Ce nom vous identifie dans le MOOC et ne peut être changé.');
});
$('.supplemental-link').initialize(function(){
 $(this).html("<a href='/honor'>Voir les conditions générales d'utilisation</a>");
});
$('#register-email').initialize(function(){
 $(this).change(function(){
    if( ($(this).val().toLowerCase().indexOf("grdf.fr")>-1) || ($(this).val().toLowerCase().indexOf("external.grdf.fr")>-1) || ($(this).val().toLowerCase().indexOf("grtgaz.com")>-1) || ($(this).val().toLowerCase().indexOf("external.grtgaz.com")>-1) || ($(this).val().toLowerCase().indexOf("storengy.com")>-1) || ($(this).val().toLowerCase().indexOf("external.storengy.com")>-1) || ($(this).val().toLowerCase().indexOf("elengy.com")>-1)|| ($(this).val().toLowerCase().indexOf("external.elengy.com")>-1) ){
      $(".register-button").css('display','none');
      $(".form-field").css('display','none');
      alert("Merci d'utiliser Chrome ou Mozilla Firefox et de vous connecter avec le bouton de votre entreprise");
    }
 });
});
}
